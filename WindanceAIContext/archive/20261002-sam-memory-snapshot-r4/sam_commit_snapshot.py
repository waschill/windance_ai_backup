"""Staged immutable commit preparation; no network or credential handling."""
import hashlib,json
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS sam_commit_snapshots(
 date_key TEXT PRIMARY KEY,input_sha256 TEXT NOT NULL,
 prepared_json TEXT,prepared_sha256 TEXT);'''
class SnapshotHeld(RuntimeError):pass
def encoded(value):
    result=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    if len(result.encode())>1048576:raise SnapshotHeld('Commit snapshot exceeds bound')
    return result
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def begin(connect,date_key,inputs):
    expected=digest(encoded(inputs))
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT input_sha256,prepared_json,prepared_sha256 FROM sam_commit_snapshots WHERE date_key=?',(date_key,)).fetchone()
        if row:
            if row[0]!=expected:raise SnapshotHeld('Schedule changed; reconcile existing commit before replacing it')
            if row[1] is not None:
                if digest(row[1])!=row[2]:raise SnapshotHeld('Prepared commit integrity mismatch')
                return json.loads(row[1])
        else:c.execute('INSERT INTO sam_commit_snapshots VALUES(?,?,NULL,NULL)',(date_key,expected))
        c.commit()
    return None
def freeze(connect,date_key,inputs,prepared):
    expected=digest(encoded(inputs));payload=encoded(prepared)
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT input_sha256,prepared_json,prepared_sha256 FROM sam_commit_snapshots WHERE date_key=?',(date_key,)).fetchone()
        if not row or row[0]!=expected:raise SnapshotHeld('Commit input binding missing or changed')
        if row[1] is not None:
            if digest(row[1])!=row[2] or row[1]!=payload:raise SnapshotHeld('Another preparation exists; reconcile before replacing it')
        else:c.execute('UPDATE sam_commit_snapshots SET prepared_json=?,prepared_sha256=? WHERE date_key=?',(payload,digest(payload),date_key))
        c.commit()
    return prepared
