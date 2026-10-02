"""Autonomy-only mailbox intent. No send capability or automatic uncertainty reset."""
import hashlib,json
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS email_action_intents (
 operation_key TEXT PRIMARY KEY,request_sha256 TEXT NOT NULL,action TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('unconfirmed','confirmed')),receipt_json TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,confirmed_at TEXT);
CREATE TABLE IF NOT EXISTS email_draft_recovery_evidence (
 operation_key TEXT PRIMARY KEY,marker TEXT NOT NULL,fingerprint TEXT NOT NULL,
 source_message_id TEXT NOT NULL,expected_thread TEXT,evidence_version INTEGER NOT NULL DEFAULT 1,
 reconciled_at TEXT);'''
class OutcomeHeld(RuntimeError):pass
def operation_key(owner,message_id):
    if owner!='william' or not isinstance(message_id,str) or not message_id.strip() or len(message_id)>500:raise ValueError('Scoped message identity required')
    return hashlib.sha256(json.dumps([owner,message_id],separators=(',',':')).encode()).hexdigest()
def report_state(connect,owner):
    if owner!='william':raise ValueError('Existing William autonomy scope required')
    with closing(connect()) as c:
        rows=c.execute('SELECT operation_key,state FROM email_action_intents').fetchall()
    return {'keys':{r[0] for r in rows},'unconfirmed':sum(r[1]=='unconfirmed' for r in rows)}
def install(c):
    if c.in_transaction:raise ValueError('Clean schema connection required')
    c.executescript(SCHEMA);c.commit()
def perform(connect,owner,message_id,action,request,callback,*,draft_evidence=None):
    if owner!='william' or action not in {'trash','draft'}:raise ValueError('Only existing William autonomy scope supported')
    if not isinstance(message_id,str) or not message_id.strip() or len(message_id)>500:raise ValueError('Message identity required')
    key=operation_key(owner,message_id)
    digest=hashlib.sha256(json.dumps([action,request],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT request_sha256,action,state,receipt_json FROM email_action_intents WHERE operation_key=?',(key,)).fetchone()
        if row:
            c.rollback()
            if row[0]!=digest or row[1]!=action:raise OutcomeHeld('A different action for this message is already recorded; reconcile first')
            if row[2]!='confirmed':raise OutcomeHeld('An earlier action has an unconfirmed outcome; do not repeat it')
            return json.loads(row[3])
        c.execute("INSERT INTO email_action_intents(operation_key,request_sha256,action,state) VALUES(?,?,?,'unconfirmed')",(key,digest,action))
        if draft_evidence is not None:
            if action!='draft':raise ValueError('Draft evidence only')
            c.execute('INSERT INTO email_draft_recovery_evidence(operation_key,marker,fingerprint,source_message_id,expected_thread) VALUES(?,?,?,?,?)',(key,draft_evidence['marker'],draft_evidence['fingerprint'],message_id,draft_evidence['thread_id']))
        c.commit()
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

def perform_recoverable_draft(connect,owner,message_id,request,create_raw):
    from gmail_draft_recovery import prepare
    if set(request)!={'to','subject','body','thread_id'} or any(not isinstance(request[x],str) for x in ['to','subject','body']):raise ValueError('Exact draft payload required')
    if request['thread_id'] is not None and not isinstance(request['thread_id'],str):raise ValueError('Thread identity must be text')
    prepared=prepare(operation_key(owner,message_id),request['to'],request['subject'],request['body'])
    evidence={'marker':prepared['marker'],'fingerprint':prepared['fingerprint'],'thread_id':request['thread_id']}
    return perform(connect,owner,message_id,'draft',request,lambda:create_raw(prepared['raw'],request['thread_id']),draft_evidence=evidence)

def reconcile_draft(connect,key,service):
    from gmail_draft_recovery import inspect,marker
    expected_marker=marker(key)
    with closing(connect()) as c:
        row=c.execute('''SELECT i.request_sha256,i.state,e.marker,e.fingerprint,e.expected_thread,e.evidence_version
          FROM email_action_intents i JOIN email_draft_recovery_evidence e USING(operation_key)
          WHERE i.operation_key=? AND i.action='draft' ''',(key,)).fetchone()
    if not row or row[2]!=expected_marker or row[5]!=1:return {'state':'held','reason':'missing_bound_evidence'}
    if row[1]!='unconfirmed':return {'state':'unchanged','reason':'already_confirmed'}
    observation=inspect(service,key,row[3],row[4])
    if observation['state']!='matched':return observation
    receipt={'draft_created':True,'id':observation['draft_id']}
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        current=c.execute('''SELECT i.request_sha256,i.state,e.marker,e.fingerprint,e.expected_thread,e.evidence_version
          FROM email_action_intents i JOIN email_draft_recovery_evidence e USING(operation_key)
          WHERE i.operation_key=? AND i.action='draft' ''',(key,)).fetchone()
        if current is None or tuple(current)!=tuple(row):c.rollback();return {'state':'held','reason':'local_evidence_changed'}
        c.execute("UPDATE email_action_intents SET state='confirmed',receipt_json=?,confirmed_at=CURRENT_TIMESTAMP WHERE operation_key=? AND state='unconfirmed'",(json.dumps(receipt),key))
        c.execute('UPDATE email_draft_recovery_evidence SET reconciled_at=CURRENT_TIMESTAMP WHERE operation_key=?',(key,));c.commit()
    return {'state':'confirmed','evidence':'exact_existing_draft','remote_writes':0}
