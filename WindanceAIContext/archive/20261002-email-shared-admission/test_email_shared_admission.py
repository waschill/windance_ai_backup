"""Cross-path uncertainty blocks a second effect; confirmation releases atomically."""
import json,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from email_action_intent import SCHEMA as AUTO_SCHEMA,perform as automatic,OutcomeHeld
from email_approval_selection import SCHEMA as SELECTION_SCHEMA
from email_approved_item_intent import SCHEMA as ITEM_SCHEMA,perform as approved,ItemHeld
from email_mailbox_admission import MailboxHeld
results=[]
for mode in ['automatic_unknown','approved_unknown','confirmed_then_other','receipt_commit_failure']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db';effects=[]
  def connect():return sqlite3.connect(path)
  with closing(connect()) as c:
   c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)');c.executescript(AUTO_SCHEMA+SELECTION_SCHEMA+ITEM_SCHEMA)
   c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES('fixture','gmail.delete',?,'executing','fixture')",(json.dumps({'message_id':'other-message'}),))
   if mode=='receipt_commit_failure':c.execute("CREATE TRIGGER fail_confirm BEFORE UPDATE ON email_action_intents BEGIN SELECT RAISE(ABORT,'fixture'); END")
   c.commit()
  def auto_effect():
   effects.append('automatic')
   if mode=='automatic_unknown':raise TimeoutError('lost')
   return {'trashed':True,'id':'message'}
  def approved_effect(item):
   effects.append('approved')
   if mode=='approved_unknown':raise TimeoutError('lost')
   return {'trashed':True,'id':'other-message'}
  def a():return automatic(connect,'william','message','trash',{},auto_effect)
  def b():return approved(connect,'fixture',0,approved_effect,lambda item,result:result)
  first,second=(b,a) if mode=='approved_unknown' else (a,b)
  try:first()
  except (OutcomeHeld,ItemHeld):assert mode!='confirmed_then_other'
  if mode=='confirmed_then_other':second();assert effects==['automatic','approved']
  else:
   try:second()
   except MailboxHeld:pass
   else:raise AssertionError('Other path bypassed mutation hold')
   assert len(effects)==1
  with closing(connect()) as c:
   holds=c.execute('SELECT COUNT(*) FROM email_mailbox_admission').fetchone()[0]
   assert holds==(0 if mode=='confirmed_then_other' else 1)
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  results.append({'case':mode,'synthetic_effects':effects,'retained_holds':holds})
print(json.dumps({'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Two staged journal paths only; mailbox-wide conservative serialization. Undo/direct legacy writers, startup backfill, operator resolution and full Harness composition remain.'}))
