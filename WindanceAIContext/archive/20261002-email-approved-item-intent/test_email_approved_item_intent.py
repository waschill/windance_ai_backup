"""Partial batch, confirmed reuse, selected-item authority and payload drift."""
import json,sqlite3,tempfile
from pathlib import Path
from contextlib import closing
from email_approval_selection import SCHEMA as SELECTION_SCHEMA,claim
from email_approved_item_intent import SCHEMA,perform,ItemHeld
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'fixture.db'
 def connect():return sqlite3.connect(path,timeout=3)
 original={'id':'root','action':'gmail.batch','requested_at':'time','payload_json':json.dumps({'actions':[{'action':'gmail.delete','message_id':f'fixture-{i}'} for i in range(3)]})}
 with closing(connect()) as c:
  c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)');c.executescript(SELECTION_SCHEMA+SCHEMA)
  c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES(?,?,?,'pending',?)",(original['id'],original['action'],original['payload_json'],original['requested_at']));c.commit()
 claim(connect,original,[0,1],[],lambda a:True,lambda:'time')
 calls=[]
 def execute(item):
  calls.append(item['message_id'])
  if item['message_id']=='fixture-1':raise TimeoutError('PRIVATE_SENTINEL')
  return {'trashed':True,'id':item['message_id']}
 def validate(item,result):
  assert result=={'trashed':True,'id':item['message_id']};return result
 first=perform(connect,'root',0,execute,validate)
 assert perform(connect,'root',0,execute,validate)==first
 for _ in range(2):
  try:perform(connect,'root',1,execute,validate)
  except ItemHeld as e:assert 'PRIVATE_SENTINEL' not in str(e)
  else:raise AssertionError('Uncertain result reused')
 try:perform(connect,'root',2,execute,validate)
 except ItemHeld:pass
 else:raise AssertionError('Unselected item executed')
 assert calls==['fixture-0','fixture-1']
 with closing(connect()) as c:
  states=c.execute('SELECT root_item_index,state FROM email_approved_item_intents ORDER BY root_item_index').fetchall()
  assert states==[(0,'confirmed'),(1,'unconfirmed')]
  changed=json.loads(original['payload_json']);changed['actions'][0]['message_id']='changed';c.execute('UPDATE approvals SET payload_json=? WHERE id=\'root\'',(json.dumps(changed),));c.commit()
 try:perform(connect,'root',0,execute,validate)
 except ItemHeld:pass
 else:raise AssertionError('Changed action reused')
 assert calls==['fixture-0','fixture-1']
print(json.dumps({'partial_batch_states':states,'synthetic_effects':len(calls),'confirmed_item_reused_without_effect':True,'uncertain_item_held':True,'unselected_item_denied':True,'changed_payload_denied':True,'actual_mailbox_calls':0,'production_changes':False,'limits':'Internal component only. Validator is caller-supplied; real per-action validators, cross-path mailbox admission, auth, schema/handler integration and crash recovery remain.'}))
