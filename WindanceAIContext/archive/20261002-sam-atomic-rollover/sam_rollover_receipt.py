"""Atomic local rollover plus durable result; caller supplies transaction-aware work."""
import hashlib,json
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS sam_rollover_receipts(
 date_key TEXT PRIMARY KEY,input_sha256 TEXT NOT NULL,
 result_json TEXT NOT NULL,result_sha256 TEXT NOT NULL);'''
class RolloverHeld(RuntimeError):pass
def encode(value):
    result=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    if len(result.encode())>1048576:raise RolloverHeld('Rollover evidence exceeds bound')
    return result
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def run_once(connect,date_key,inputs,perform):
    expected=digest(encode(inputs))
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT input_sha256,result_json,result_sha256 FROM sam_rollover_receipts WHERE date_key=?',(date_key,)).fetchone()
        if row:
            if row[0]!=expected:raise RolloverHeld('Rollover input changed; explicit reconciliation required')
            if digest(row[1])!=row[2]:raise RolloverHeld('Rollover receipt integrity mismatch')
            return json.loads(row[1])
        result=perform(db)
        if not db.in_transaction:raise RolloverHeld('Rollover callback escaped its transaction')
        payload=encode(result)
        db.execute('INSERT INTO sam_rollover_receipts VALUES(?,?,?,?)',(date_key,expected,payload,digest(payload)))
        db.commit()
        return result
