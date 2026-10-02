"""Staged SAM history-create intent journal. No remote client or automatic retry."""
import datetime,hashlib,json
from contextlib import closing


class Unconfirmed(RuntimeError):pass
class Conflict(RuntimeError):pass


def install(connection):
    if connection.in_transaction:raise ValueError('Clean schema connection required')
    connection.execute('''CREATE TABLE IF NOT EXISTS sam_history_intents (
      operation_key TEXT PRIMARY KEY,payload_sha256 TEXT NOT NULL,
      state TEXT NOT NULL CHECK(state IN ('unconfirmed','confirmed')),
      record_id INTEGER,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      confirmed_at TEXT)''')
    connection.commit()


def perform(connect,date_key,item_id,horse_id,service_type,details,send):
    date_key=datetime.date.fromisoformat(date_key).isoformat()
    if type(item_id) is int and item_id>0:item_id=str(item_id)
    if service_type not in {'Farrier','Veterinarian'} or not isinstance(item_id,str) or not item_id or item_id!=item_id.strip() or len(item_id)>200 or type(horse_id) is not int or horse_id<=0:
        raise ValueError('Narrow completed-service identity required')
    if not isinstance(details,str) or not details.strip() or len(' '.join(details.split()))>500:
        raise ValueError('Bounded service details required')
    key=json.dumps([date_key,item_id,service_type],separators=(',',':'))
    digest=hashlib.sha256(json.dumps([horse_id,service_type,date_key,' '.join(details.split())],separators=(',',':')).encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT payload_sha256,state,record_id FROM sam_history_intents WHERE operation_key=?',(key,)).fetchone()
        if row:
            c.rollback()
            if row[0]!=digest:raise Conflict('History operation payload changed; reconciliation required')
            if row[1]!='confirmed':raise Unconfirmed('Prior history outcome is unconfirmed; do not repeat the write')
            return {'status':'ok','record_id':row[2]}
        c.execute("INSERT INTO sam_history_intents(operation_key,payload_sha256,state) VALUES(?,?,'unconfirmed')",(key,digest))
        c.commit()
    # Durable unconfirmed intent precedes every remote invocation, including a
    # crash before send. No elapsed-time or retry-count transition releases it.
    try:
        result=send()
        if not isinstance(result,dict) or result.get('status')!='ok' or type(result.get('record_id')) is not int or result['record_id']<=0:
            raise ValueError('Invalid remote receipt')
        with closing(connect()) as c:
            c.execute('BEGIN IMMEDIATE')
            changed=c.execute("UPDATE sam_history_intents SET state='confirmed',record_id=?,confirmed_at=CURRENT_TIMESTAMP WHERE operation_key=? AND payload_sha256=? AND state='unconfirmed'",(result['record_id'],key,digest)).rowcount
            if changed!=1:raise RuntimeError('Intent changed')
            c.commit()
        return {'status':'ok','record_id':result['record_id']}
    except Exception:
        raise Unconfirmed('History outcome could not be durably confirmed; reconciliation required') from None
