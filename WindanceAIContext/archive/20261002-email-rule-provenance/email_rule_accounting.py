"""Private rule provenance reserved with intent; local confirmed-effect repair only."""
import hashlib,json
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS email_rule_provenance (
 operation_key TEXT PRIMARY KEY,request_sha256 TEXT NOT NULL,evidence_json TEXT NOT NULL,
 applied INTEGER NOT NULL DEFAULT 0 CHECK(applied IN (0,1)),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS email_rule_provenance_pending ON email_rule_provenance(applied);'''
def evidence(rule_key,rule_action,item,importance,original_state):
    result={'rule_key':rule_key,'rule_action':rule_action,'id':item.get('id'),
            'thread_id':item.get('thread_id') or '', 'sender':item.get('from') or '',
            'subject':item.get('subject') or '', 'importance':importance,'original_state':original_state}
    validate(result);return result
def validate(value):
    keys={'rule_key','rule_action','id','thread_id','sender','subject','importance','original_state'}
    if type(value) is not dict or set(value)!=keys:raise ValueError('Exact rule evidence required')
    limits={'rule_key':320,'id':500,'thread_id':500,'sender':1024,'subject':2048,'rule_action':20,'importance':20,'original_state':10}
    if any(type(value[k]) is not str or len(value[k])>limit for k,limit in limits.items()):raise ValueError('Bounded rule evidence required')
    if not value['rule_key'] or not value['id'] or value['rule_action'] not in ('always_delete','notify_delete') or value['importance'] not in ('important','normal') or value['original_state'] not in ('read','unread'):raise ValueError('Invalid rule evidence')
def expected(value):
    validate(value)
    key=hashlib.sha256(json.dumps(['william',value['id']],separators=(',',':')).encode()).hexdigest()
    request={'sender_rule':value['rule_key'],'rule_action':value['rule_action']}
    digest=hashlib.sha256(json.dumps(['trash',request],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return key,digest
def reserve(c,key,digest,value):
    if not c.in_transaction:raise ValueError('Intent transaction required')
    if (key,digest)!=expected(value):raise ValueError('Rule provenance binding mismatch')
    row=c.execute('SELECT request_sha256,action,state FROM email_action_intents WHERE operation_key=?',(key,)).fetchone()
    if row is None or tuple(row)!=(digest,'trash','unconfirmed'):raise ValueError('Matching new intent required')
    c.execute('INSERT INTO email_rule_provenance(operation_key,request_sha256,evidence_json) VALUES(?,?,?)',(key,digest,json.dumps(value,sort_keys=True)))
def require_existing(c,key,digest,value):
    if (key,digest)!=expected(value):raise ValueError('Rule provenance binding mismatch')
    row=c.execute('SELECT request_sha256,evidence_json FROM email_rule_provenance WHERE operation_key=?',(key,)).fetchone()
    if row is None or row[0]!=digest or expected(json.loads(row[1]))!=(key,digest):raise ValueError('Existing rule provenance unavailable')
def _apply(c,key):
    row=c.execute('''SELECT p.request_sha256,p.evidence_json,p.applied,p.created_at,i.request_sha256,i.action,i.state,i.receipt_json
      FROM email_rule_provenance p JOIN email_action_intents i USING(operation_key) WHERE p.operation_key=?''',(key,)).fetchone()
    if row is None:raise ValueError('Rule provenance missing')
    value=json.loads(row[1]);validate(value)
    receipt=json.loads(row[7] or '{}')
    if expected(value)!=(key,row[0]) or row[0]!=row[4] or row[5]!='trash' or row[6]!='confirmed' or type(receipt) is not dict or receipt.get('trashed') is not True or receipt.get('id')!=value['id']:raise ValueError('Confirmed rule evidence required')
    if row[2]==1:return False
    recorded=c.execute('INSERT OR IGNORE INTO email_sender_rule_receipts VALUES(?,?,?,?)',(key,value['rule_key'],value['rule_action'],row[3])).rowcount==1
    existing=c.execute('SELECT sender_key,rule_action FROM email_sender_rule_receipts WHERE operation_key=?',(key,)).fetchone()
    if tuple(existing)!=(value['rule_key'],value['rule_action']):raise ValueError('Rule accounting conflict')
    if recorded:
        c.execute('UPDATE max_email_sender_rules SET last_matched_at=?,match_count=match_count+1 WHERE sender_email=? AND action=?',(row[3],value['rule_key'],value['rule_action']))
        c.execute('''INSERT INTO max_email_tracking
          (message_id,thread_id,sender,subject,first_seen_at,last_seen_at,last_gmail_state,max_state,importance,follow_up_state,notes)
          VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(message_id) DO UPDATE SET
          last_seen_at=excluded.last_seen_at,last_gmail_state=excluded.last_gmail_state,max_state=excluded.max_state,
          follow_up_state=excluded.follow_up_state,notes=COALESCE(max_email_tracking.notes || char(10),'') || excluded.notes''',
          (value['id'],value['thread_id'],value['sender'],value['subject'],row[3],row[3],value['original_state'],
           'auto_deleted_by_sender_rule',value['importance'],value['rule_action'],row[3]+': Confirmed Trash under saved sender rule '+value['rule_key']+'.'))
    c.execute('UPDATE email_rule_provenance SET applied=1 WHERE operation_key=? AND applied=0',(key,))
    return recorded
def account(connect,key):
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE');result=_apply(c,key);c.commit();return result
def reconcile(connect,limit=20):
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('Bounded accounting limit required')
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        keys=[r[0] for r in c.execute('''SELECT p.operation_key FROM email_rule_provenance p JOIN email_action_intents i USING(operation_key)
          WHERE p.applied=0 AND i.state='confirmed' ORDER BY p.rowid LIMIT ?''',(limit,))]
        for key in keys:_apply(c,key)
        c.commit();return len(keys)
