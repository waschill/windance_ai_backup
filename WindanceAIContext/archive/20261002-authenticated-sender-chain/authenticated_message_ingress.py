"""Staged adapter-authenticated manager intake. No production credentials or routes.

Authenticates a trusted adapter, not the human independently of that adapter.
The SAL adapter must enforce its installed sender/direct-chat checks before use.
"""
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import sqlite3
import time
from aiohttp import web


@dataclass(frozen=True)
class Adapter:
    issuer: str
    credential: str = field(repr=False)
    owners: frozenset[str]
    channel: str
    notify: bool = False


class Intake:
    def __init__(self, adapters, connect, validate_message):
        if not callable(validate_message):
            raise ValueError('Server content policy required')
        self.validate_message = validate_message
        self.adapters = tuple(adapters)
        self.connect = connect
        if len({a.issuer for a in self.adapters}) != len(self.adapters):
            raise ValueError('Duplicate issuer')
        if len({a.credential for a in self.adapters}) != len(self.adapters):
            raise ValueError('Duplicate credential')
        for a in self.adapters:
            if not a.issuer or not a.credential or not a.channel or not a.owners or not a.owners <= {'william', 'shawn'}:
                raise ValueError('Invalid adapter policy')

    @staticmethod
    def install(c):
        c.execute('''CREATE TABLE IF NOT EXISTS authenticated_message_sources (
          message_id TEXT PRIMARY KEY REFERENCES messages(id), issuer TEXT NOT NULL,
          source_id TEXT NOT NULL, owner TEXT NOT NULL, channel TEXT NOT NULL,
          text_sha256 TEXT NOT NULL, binding_sha256 TEXT NOT NULL,
          UNIQUE(issuer,channel,source_id))''')
        c.commit()

    async def handle(self, request):
        try:
            return await self._handle(request)
        except sqlite3.Error:
            raise web.HTTPServiceUnavailable(text='Intake storage unavailable; retry the same source') from None

    async def _handle(self, request):
        auth = request.headers.get('Authorization', '')
        matches = [a for a in self.adapters if auth.startswith('Bearer ') and
                   hmac.compare_digest(a.credential.encode(), auth[7:].encode())]
        if len(matches) != 1:
            raise web.HTTPForbidden(text='Authenticated adapter required')
        adapter = matches[0]
        try:
            body = await request.json()
        except (ValueError, UnicodeError):
            raise web.HTTPBadRequest(text='Valid source envelope required') from None
        if not isinstance(body, dict) or set(body) != {'owner', 'source_id', 'message'}:
            raise web.HTTPUnprocessableEntity(text='Exact source envelope required')
        owner, source_id, message = (body[k] for k in ('owner', 'source_id', 'message'))
        if not isinstance(owner, str) or owner not in adapter.owners:
            raise web.HTTPForbidden(text='Adapter owner scope denied')
        if not isinstance(source_id, str) or not source_id or len(source_id) > 200 or source_id != source_id.strip():
            raise web.HTTPUnprocessableEntity(text='Stable source identifier required')
        if not isinstance(message, str) or not message.strip() or len(message) > 100000:
            raise web.HTTPUnprocessableEntity(text='Message required within size limit')
        if not self.validate_message(message):
            return web.json_response({'status':'rejected','reason':'content_policy','stored':False},status=422)
        identity = json.dumps([adapter.issuer, adapter.channel, source_id], separators=(',', ':'))
        mid = 'AUTH-' + hashlib.sha256(identity.encode()).hexdigest()
        digest = hashlib.sha256(message.encode()).hexdigest()
        binding = hashlib.sha256(json.dumps([identity, owner, digest], separators=(',', ':')).encode()).hexdigest()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            prior = c.execute('SELECT binding_sha256 FROM authenticated_message_sources WHERE message_id=?', (mid,)).fetchone()
            existing = c.execute('SELECT request,owner,channel FROM messages WHERE id=?', (mid,)).fetchone()
            if prior:
                if prior[0] != binding or not existing or tuple(existing) != (message, owner.title(), adapter.channel):
                    raise web.HTTPConflict(text='Source identity conflict')
            else:
                if existing:
                    raise web.HTTPConflict(text='Unattested message identity collision')
                now = time.time()
                # Session and delivery policy are server-owned, not envelope fields.
                c.execute('''INSERT INTO messages
                  (id,request,channel,session,status,answer,created,updated,notify,receipt,owner)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                  (mid, message, adapter.channel, owner, 'queued', '', now, now, int(adapter.notify), None, owner.title()))
                c.execute('INSERT INTO authenticated_message_sources VALUES(?,?,?,?,?,?,?)',
                          (mid, adapter.issuer, source_id, owner, adapter.channel, digest, binding))
        return web.json_response({'id': mid, 'source_ref': 'manager-message:' + mid,
                                  'status': 'accepted', 'replayed': bool(prior)}, status=202)


def authenticated_source_loader(connect):
    """Memory source reader accepts attested rows only; no legacy fallback."""
    from source_bound_facts import Source
    def load(owner, reference):
        if not isinstance(reference, str) or not reference.startswith('manager-message:'):
            raise KeyError('Unsupported source')
        mid = reference[len('manager-message:'):]
        with connect() as c:
            row = c.execute('''SELECT m.owner,m.channel,m.request,a.owner,a.channel,a.text_sha256
              FROM messages m JOIN authenticated_message_sources a ON a.message_id=m.id
              WHERE m.id=?''', (mid,)).fetchone()
        if row is None:
            raise KeyError('Authenticated source unavailable')
        if row[0].lower() != owner or row[3] != owner or row[1] != row[4]:
            raise PermissionError('Source ownership mismatch')
        if hashlib.sha256(row[2].encode()).hexdigest() != row[5]:
            raise KeyError('Source changed')
        return Source(owner, row[1], reference, row[2])
    return load
