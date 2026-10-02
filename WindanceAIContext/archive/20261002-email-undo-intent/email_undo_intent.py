"""Internal reference-bound reversal journal; no automatic retry/reset."""
import hashlib,json
from contextlib import closing
from email_mailbox_admission import SCHEMA as ADMISSION_SCHEMA,claim,release
SCHEMA=ADMISSION_SCHEMA+'''CREATE TABLE IF NOT EXISTS email_undo_intents (
 action_id INTEGER PRIMARY KEY,request_sha256 TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('unconfirmed','confirmed')),receipt_json TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,confirmed_at TEXT);'''
class UndoHeld(RuntimeError):pass
def perform(connect,action_id,expected_ref,execute,now):
    if type(action_id) is not int or action_id<=0:raise ValueError('Saved action identity required')
    query='SELECT run_id,ordinal,message_id,action,draft_id,reversed_at,reversal_result FROM email_autonomy_actions WHERE id=?'
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE');row=c.execute(query,(action_id,)).fetchone()
        if not row or tuple(row[:3])!=(expected_ref['run_id'],expected_ref['ordinal'],expected_ref['message_id']):raise UndoHeld('Saved report/action identity changed')
        data={'action_id':action_id,'run_id':row[0],'ordinal':row[1],'message_id':row[2],'action':row[3],'draft_id':row[4]}
        if row[3] not in {'archived','trashed','draft_created'} or (row[3]=='draft_created' and not row[4]):raise UndoHeld('No supported reversible action')
        digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest();reservation='undo:'+digest
        prior=c.execute('SELECT request_sha256,state,receipt_json FROM email_undo_intents WHERE action_id=?',(action_id,)).fetchone()
        if prior:
            if prior[0]!=digest or prior[1]!='confirmed':raise UndoHeld('Earlier reversal outcome requires reconciliation')
            receipt=json.loads(prior[2])
            if not row[5] or row[6]!=receipt['reversal_result']:raise UndoHeld('Saved reversal receipt changed')
            return receipt
        if row[5]:raise UndoHeld('Action already reversed outside this journal')
        claim(c,reservation)
        c.execute("INSERT INTO email_undo_intents(action_id,request_sha256,state) VALUES(?,?,'unconfirmed')",(action_id,digest));c.commit()
    try:
        result=execute(data)
        draft=data['action']=='draft_created';identity=data['draft_id'] if draft else data['message_id'];flag='draft_deleted' if draft else 'restored_to_inbox'
        if not isinstance(result,dict) or result.get(flag) is not True or result.get('id')!=identity:raise ValueError('Missing matching reversal receipt')
        description={'archived':'restored the message to Inbox','trashed':'restored the message from Trash to Inbox','draft_created':'deleted the unsent draft; the original message was untouched'}[data['action']]
        receipt={'reversal_result':description,'id':identity,flag:True}
        with closing(connect()) as c:
            c.execute('BEGIN IMMEDIATE');current=c.execute(query,(action_id,)).fetchone()
            if not current or tuple(current[:5])!=tuple(row[:5]) or current[5]:raise UndoHeld('Reversal source changed before confirmation')
            if c.execute("UPDATE email_undo_intents SET state='confirmed',receipt_json=?,confirmed_at=? WHERE action_id=? AND request_sha256=? AND state='unconfirmed'",(json.dumps(receipt),now(),action_id,digest)).rowcount!=1:raise UndoHeld('Reversal intent changed')
            if c.execute('UPDATE email_autonomy_actions SET reversed_at=?,reversal_result=? WHERE id=? AND reversed_at IS NULL',(now(),description,action_id)).rowcount!=1:raise UndoHeld('Reversal record changed')
            release(c,reservation);c.commit()
        return receipt
    except Exception:raise UndoHeld('Reversal outcome unconfirmed; reconcile before another attempt') from None
