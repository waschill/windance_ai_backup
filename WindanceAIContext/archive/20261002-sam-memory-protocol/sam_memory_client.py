"""Staged durable SAM memory request; no credentials or network implementation."""
import hashlib,json,uuid
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS sam_memory_requests(
 date_key TEXT NOT NULL,expected_revision INTEGER NOT NULL,event_id TEXT NOT NULL UNIQUE,
 payload_sha256 TEXT NOT NULL,payload_json TEXT NOT NULL,state TEXT NOT NULL,
 receipt_json TEXT,PRIMARY KEY(date_key,expected_revision));'''
class MemoryHeld(RuntimeError):pass
def validate(result,payload,event,expected_revision):
    content=hashlib.sha256(payload['value'].encode()).hexdigest()
    if not isinstance(result,dict) or result.get('status')!='ok' or result.get('event_id')!=event or result.get('producer')!='sam' or result.get('scope')!='business' or result.get('date')!=payload['key'] or result.get('content_sha256')!=content or type(result.get('revision')) is not int or result['revision']!=expected_revision+1 or result.get('superseded') is not False:
        raise MemoryHeld('No matching source receipt; local day must remain uncommitted')
    return {k:result[k] for k in ('status','event_id','producer','scope','date','content_sha256','revision','superseded')}
def submit(connect,payload,transport,*,expected_revision=0):
    if type(expected_revision) is not int or not 0<=expected_revision<2**63-1:raise ValueError('Expected revision required')
    date=payload['key'];encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)
    if len(encoded.encode())>131072:raise ValueError('Bounded payload required')
    digest=hashlib.sha256(encoded.encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT event_id,payload_sha256,state,receipt_json FROM sam_memory_requests WHERE date_key=? AND expected_revision=?',(date,expected_revision)).fetchone()
        if row:
            if row[1]!=digest:raise MemoryHeld('Pending or prior request has different content; reconcile before replacing')
            event=row[0]
            if row[2]=='confirmed':return validate(json.loads(row[3]),payload,event,expected_revision)
        else:
            event=uuid.uuid4().hex
            c.execute("INSERT INTO sam_memory_requests VALUES(?,?,?,?,?,'pending',NULL)",(date,expected_revision,event,digest,encoded))
        c.commit()
    result=transport({'event_id':event,'expected_revision':expected_revision,'payload':payload})
    receipt=validate(result,payload,event,expected_revision)
    saved=json.dumps(receipt,sort_keys=True,separators=(',',':'))
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT event_id,payload_sha256,state,receipt_json FROM sam_memory_requests WHERE date_key=? AND expected_revision=?',(date,expected_revision)).fetchone()
        if not row or row[0]!=event or row[1]!=digest or (row[2]=='confirmed' and row[3]!=saved):raise MemoryHeld('Local request changed; reconcile before committing')
        c.execute("UPDATE sam_memory_requests SET state='confirmed',receipt_json=? WHERE event_id=?",(saved,event));c.commit()
    return receipt
