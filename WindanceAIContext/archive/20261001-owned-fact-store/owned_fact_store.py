"""Candidate canonical facts. Callers must supply an authenticated principal.

This module does not authenticate HTTP users or infer sharing from source text.
No legacy migration, embedding, mirror, network access, or dispatch is performed.
"""
import hashlib
import json
import sqlite3
from contextlib import contextmanager


class Conflict(ValueError):
    pass


def principal(value):
    if not isinstance(value, str) or value not in {'william', 'shawn'}:
        raise PermissionError('Verified supported principal required')
    return value


def install(connection):
    """Explicit schema installation; never called implicitly by a write."""
    if connection.in_transaction:
        raise RuntimeError('Schema requires a clean connection')
    connection.executescript('''
    BEGIN IMMEDIATE;
    CREATE TABLE IF NOT EXISTS owned_facts (
      owner TEXT NOT NULL, scope TEXT NOT NULL CHECK(scope IN ('personal','business')),
      kind TEXT NOT NULL, fact_key TEXT NOT NULL, value TEXT,
      source_ref TEXT NOT NULL, revision INTEGER NOT NULL,
      deleted INTEGER NOT NULL CHECK(deleted IN (0,1)),
      PRIMARY KEY(owner,scope,kind,fact_key));
    CREATE TABLE IF NOT EXISTS owned_fact_events (
      owner TEXT NOT NULL, scope TEXT NOT NULL, kind TEXT NOT NULL, fact_key TEXT NOT NULL,
      revision INTEGER NOT NULL, action TEXT NOT NULL, source_ref TEXT NOT NULL,
      value_sha256 TEXT, recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(owner,scope,kind,fact_key,revision));
    CREATE TABLE IF NOT EXISTS owned_fact_grants (
      owner TEXT NOT NULL, scope TEXT NOT NULL, kind TEXT NOT NULL, fact_key TEXT NOT NULL,
      reader TEXT NOT NULL, revision INTEGER NOT NULL,
      PRIMARY KEY(owner,scope,kind,fact_key,reader));
    COMMIT;
    ''')


@contextmanager
def transaction(connection):
    if connection.in_transaction:
        raise RuntimeError('Dedicated clean connection required')
    connection.execute('BEGIN IMMEDIATE')
    try:
        yield
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def identity(owner, scope, kind, key):
    principal(owner)
    if scope not in {'personal', 'business'}:
        raise ValueError('Explicit business or personal scope required')
    if any(not isinstance(v, str) or not v.strip() or len(v) > 200 for v in (kind, key)):
        raise ValueError('Invalid fact identity')
    return owner, scope, kind, key


def read(connection, actor, owner, scope, kind, key):
    principal(actor)
    ident = identity(owner, scope, kind, key)
    row = connection.execute('''SELECT value,source_ref,revision,deleted FROM owned_facts
      WHERE owner=? AND scope=? AND kind=? AND fact_key=?''', ident).fetchone()
    if row is None or row[3]:
        return None
    if actor != owner:
        grant = connection.execute('''SELECT 1 FROM owned_fact_grants WHERE
          owner=? AND scope=? AND kind=? AND fact_key=? AND reader=? AND revision=?''',
          (*ident, actor, row[2])).fetchone()
        if scope != 'business' or not grant:
            return None
    return {'owner': owner, 'scope': scope, 'kind': kind, 'key': key,
            'value': row[0], 'source_ref': row[1], 'revision': row[2],
            'source_id': json.dumps(ident, separators=(',', ':'))}


def write(connection, actor, owner, scope, kind, key, value, source_ref,
          expected_revision=0, delete=False):
    if principal(actor) != owner:
        raise PermissionError('Only the fact owner can change it')
    ident = identity(owner, scope, kind, key)
    if not isinstance(source_ref, str) or not source_ref.strip() or len(source_ref) > 1000:
        raise ValueError('Durable source reference required')
    if not delete and (not isinstance(value, str) or not value.strip() or len(value) > 20000):
        raise ValueError('Nonempty bounded fact required')
    with transaction(connection):
        previous = connection.execute('''SELECT revision FROM owned_facts
          WHERE owner=? AND scope=? AND kind=? AND fact_key=?''', ident).fetchone()
        current = previous[0] if previous else 0
        if current != expected_revision or (delete and previous is None):
            raise Conflict('Fact changed or missing; reread before editing')
        revision = current + 1
        stored_value = None if delete else value
        connection.execute('''INSERT INTO owned_facts VALUES(?,?,?,?,?,?,?,?)
          ON CONFLICT(owner,scope,kind,fact_key) DO UPDATE SET value=excluded.value,
          source_ref=excluded.source_ref,revision=excluded.revision,deleted=excluded.deleted''',
          (*ident, stored_value, source_ref, revision, int(delete)))
        # Corrections do not silently share newly supplied content under an old grant.
        connection.execute('DELETE FROM owned_fact_grants WHERE owner=? AND scope=? AND kind=? AND fact_key=?', ident)
        digest = hashlib.sha256(value.encode()).hexdigest() if not delete else None
        connection.execute('''INSERT INTO owned_fact_events
          (owner,scope,kind,fact_key,revision,action,source_ref,value_sha256)
          VALUES(?,?,?,?,?,?,?,?)''', (*ident, revision, 'delete' if delete else 'write', source_ref, digest))
        verified = read(connection, actor, *ident)
        if (delete and verified is not None) or (not delete and (verified is None or verified['value'] != value or verified['revision'] != revision)):
            raise RuntimeError('Canonical readback failed')
    return {'revision': revision, 'deleted': delete, 'fact': verified}


def share(connection, actor, owner, scope, kind, key, reader, expected_revision, revoke=False):
    if principal(actor) != owner:
        raise PermissionError('Only the owner can grant or revoke access')
    principal(reader)
    ident = identity(owner, scope, kind, key)
    if scope != 'business' or reader == owner:
        raise ValueError('Only explicit business sharing to another owner is supported')
    with transaction(connection):
        fact = read(connection, actor, *ident)
        if fact is None or fact['revision'] != expected_revision:
            raise Conflict('Sharing requires the current live revision')
        if revoke:
            connection.execute('DELETE FROM owned_fact_grants WHERE owner=? AND scope=? AND kind=? AND fact_key=? AND reader=?', (*ident, reader))
        else:
            connection.execute('INSERT OR REPLACE INTO owned_fact_grants VALUES(?,?,?,?,?,?)', (*ident, reader, expected_revision))
