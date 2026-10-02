"""Staged narrow SAM need-clear journal: retain ambiguity, never blind retry."""
import datetime,hashlib,json
from contextlib import closing

class ClearHeld(RuntimeError):pass

def install(c):
    if c.in_transaction:raise ValueError('Clean schema connection required')
    c.execute('''CREATE TABLE IF NOT EXISTS sam_clear_intents (
      operation_key TEXT PRIMARY KEY,payload_sha256 TEXT NOT NULL,
      state TEXT NOT NULL CHECK(state IN ('unconfirmed','confirmed')),
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,confirmed_at TEXT)''')
    c.commit()

def perform(connect,date_key,item_id,horse_id,service_type,history_id,send):
    date_key=datetime.date.fromisoformat(date_key).isoformat()
    if service_type not in {'Farrier','Veterinarian'} or not isinstance(item_id,str) or not item_id or item_id!=item_id.strip() or len(item_id)>200:
        raise ValueError('Narrow completed-service identity required')
    if any(type(x) is not int or x<=0 for x in [horse_id,history_id]):raise ValueError('Confirmed history and horse IDs required')
    key=json.dumps([date_key,item_id,service_type],separators=(',',':'))
    digest=hashlib.sha256(json.dumps([horse_id,history_id,service_type],separators=(',',':')).encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT payload_sha256,state FROM sam_clear_intents WHERE operation_key=?',(key,)).fetchone()
        if row:
            c.rollback()
            if row[0]!=digest:raise ClearHeld('Clear payload changed; reconciliation required')
            if row[1]!='confirmed':raise ClearHeld('Prior clear outcome unknown; do not repeat or clear a newer request')
            return {'status':'ok'}
        c.execute("INSERT INTO sam_clear_intents(operation_key,payload_sha256,state) VALUES(?,?,'unconfirmed')",(key,digest));c.commit()
    try:
        result=send()
        expected_field={'Farrier':'x_studio_needs_farrier','Veterinarian':'x_studio_needs_vet'}[service_type]
        if not isinstance(result,dict) or result.get('status')!='ok' or result.get('result') is not True or result.get('model')!='x_horses' or type(result.get('record_id')) is not int or result['record_id']!=horse_id or result.get('fields')!=[expected_field]:
            raise ValueError('Unconfirmed or mismatched remote acknowledgment')
        with closing(connect()) as c:
            c.execute('BEGIN IMMEDIATE')
            changed=c.execute("UPDATE sam_clear_intents SET state='confirmed',confirmed_at=CURRENT_TIMESTAMP WHERE operation_key=? AND payload_sha256=? AND state='unconfirmed'",(key,digest)).rowcount
            if changed!=1:raise RuntimeError('Clear intent changed')
            c.commit()
        return {'status':'ok'}
    except Exception:
        raise ClearHeld('Clear outcome could not be durably confirmed; reconciliation required') from None
