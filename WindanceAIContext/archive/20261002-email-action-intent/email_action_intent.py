"""Autonomy-only mailbox intent. No send capability or automatic uncertainty reset."""
import hashlib,json
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS email_action_intents (
 operation_key TEXT PRIMARY KEY,request_sha256 TEXT NOT NULL,action TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('unconfirmed','confirmed')),receipt_json TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,confirmed_at TEXT);'''
class OutcomeHeld(RuntimeError):pass
def install(c):
    if c.in_transaction:raise ValueError('Clean schema connection required')
    c.execute(SCHEMA);c.commit()
def perform(connect,owner,message_id,action,request,callback):
    if owner!='william' or action not in {'trash','draft'}:raise ValueError('Only existing William autonomy scope supported')
    if not isinstance(message_id,str) or not message_id.strip() or len(message_id)>500:raise ValueError('Message identity required')
    key=hashlib.sha256(json.dumps([owner,message_id],separators=(',',':')).encode()).hexdigest()
    digest=hashlib.sha256(json.dumps([action,request],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT request_sha256,action,state,receipt_json FROM email_action_intents WHERE operation_key=?',(key,)).fetchone()
        if row:
            c.rollback()
            if row[0]!=digest or row[1]!=action:raise OutcomeHeld('A different action for this message is already recorded; reconcile first')
            if row[2]!='confirmed':raise OutcomeHeld('An earlier action has an unconfirmed outcome; do not repeat it')
            return json.loads(row[3])
        c.execute("INSERT INTO email_action_intents(operation_key,request_sha256,action,state) VALUES(?,?,?,'unconfirmed')",(key,digest,action));c.commit()
    try:
        result=callback()
        if not isinstance(result,dict):raise ValueError('Missing receipt')
        if action=='trash':
            if result.get('trashed') is not True or result.get('id')!=message_id:raise ValueError('Invalid Trash receipt')
            receipt={'trashed':True,'id':message_id}
        else:
            if result.get('draft_created') is not True or not isinstance(result.get('id'),str) or not result['id'].strip():raise ValueError('Invalid draft receipt')
            receipt={'draft_created':True,'id':result['id']}
        with closing(connect()) as c:
            c.execute('BEGIN IMMEDIATE')
            changed=c.execute("UPDATE email_action_intents SET state='confirmed',receipt_json=?,confirmed_at=CURRENT_TIMESTAMP WHERE operation_key=? AND request_sha256=? AND state='unconfirmed'",(json.dumps(receipt),key,digest)).rowcount
            if changed!=1:raise RuntimeError('Intent changed')
            c.commit()
        return receipt
    except Exception:
        raise OutcomeHeld('Mailbox outcome could not be durably confirmed; reconcile before another action') from None
