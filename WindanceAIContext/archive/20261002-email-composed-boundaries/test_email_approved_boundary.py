"""Reproduce approved executor bypass with a synthetic pre-existing hold."""
import ast,hashlib,json,sqlite3,sys,tempfile
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-trash-receipt-20261002');sys.path.insert(0,str(root))
from email_action_intent import install,perform,OutcomeHeld
p=root/'agent_harness.candidate.private.py';s=p.read_text()
assert hashlib.sha256(p.read_bytes()).hexdigest()=='1e011c5263479660998b817fb423e34408ce0426a0f8e6279cf0d70cd4d85e4b'
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='execute_approved_action')
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'fixture.db'
 def connect():return sqlite3.connect(path)
 c=connect();install(c);c.close()
 def lost():raise TimeoutError('synthetic accepted effect')
 try:perform(connect,'william','fixture','trash',{},lost)
 except OutcomeHeld:pass
 calls=[]
 def trash(message_id):calls.append(message_id);return {'trashed':True,'marked_read':True,'id':message_id}
 ns={'Any':Any,'require_william_mailbox':lambda:None,'require_payload':lambda p,k:p[k],'gmail_delete_message':trash,'db':connect}
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-approved-executor>','exec'),ns)
 result=ns['execute_approved_action']('gmail.delete',{'message_id':'fixture'})
 assert calls==['fixture'] and result['result']['trashed']
 c=connect();assert c.execute('SELECT state FROM email_action_intents').fetchone()[0]=='unconfirmed';c.close()
print(json.dumps({'candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'existing_unconfirmed_intent_preserved':True,'approved_executor_called_mock_primitive_despite_hold':True,'executor_parameters':[a.arg for a in node.args.args],'actual_mailbox_calls':0,'production_changes':False,'limits':'Synthetic direct executor invocation; not an unauthenticated entry or evidence of historical repeated actions. Full approval lifecycle requires inspection.'}))
