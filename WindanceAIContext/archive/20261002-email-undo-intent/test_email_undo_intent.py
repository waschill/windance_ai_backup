"""Reference binding, lost results and atomic local reversal receipt failure."""
import json,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from email_undo_intent import SCHEMA,perform,UndoHeld
from email_mailbox_admission import is_held
results=[]
for mode in ['normal','lost_response','wrong_receipt','local_receipt_failure','wrong_reference']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db';effects=[]
  def connect():return sqlite3.connect(path)
  with closing(connect()) as c:
   c.executescript(SCHEMA+'''CREATE TABLE email_autonomy_actions(id INTEGER PRIMARY KEY,run_id TEXT,ordinal INTEGER,message_id TEXT,action TEXT,draft_id TEXT,reversed_at TEXT,reversal_result TEXT);''')
   c.execute("INSERT INTO email_autonomy_actions VALUES(1,'run',1,'message','trashed',NULL,NULL,NULL)")
   if mode=='local_receipt_failure':c.execute("CREATE TRIGGER fail_local BEFORE UPDATE ON email_autonomy_actions BEGIN SELECT RAISE(ABORT,'fixture'); END")
   c.commit()
  def execute(data):
   effects.append(data['action_id'])
   if mode=='lost_response':raise TimeoutError('PRIVATE_SENTINEL')
   return {'restored_to_inbox':True,'id':'wrong' if mode=='wrong_receipt' else 'message'}
  ref={'run_id':'wrong' if mode=='wrong_reference' else 'run','ordinal':1,'message_id':'message'}
  for _ in range(2):
   try:result=perform(connect,1,ref,execute,lambda:'fixture')
   except UndoHeld as e:assert mode!='normal' and 'PRIVATE_SENTINEL' not in str(e)
   else:assert mode=='normal' and result['restored_to_inbox']
  assert len(effects)==(0 if mode=='wrong_reference' else 1)
  assert is_held(connect)==(mode not in {'normal','wrong_reference'})
  with closing(connect()) as c:
   reversed_at=c.execute('SELECT reversed_at FROM email_autonomy_actions').fetchone()[0]
   assert bool(reversed_at)==(mode=='normal')
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  results.append({'case':mode,'synthetic_effects':len(effects),'local_reversal_confirmed':bool(reversed_at)})
print(json.dumps({'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Internal reversal journal only; actual restore/delete-draft helper receipts, authenticated undo handler, full schema/recovery and authoritative reconciliation remain.'}))
