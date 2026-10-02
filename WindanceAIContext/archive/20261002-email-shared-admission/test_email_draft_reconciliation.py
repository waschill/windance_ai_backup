"""Durable intent -> lost response -> read-only exact draft confirmation."""
import base64,json,sqlite3,tempfile
from pathlib import Path
from email_action_intent import install,perform_recoverable_draft,reconcile_draft,operation_key,OutcomeHeld
results=[]
class ClosingConnection(sqlite3.Connection):
 def __exit__(self,*args):
  try:return super().__exit__(*args)
  finally:self.close()
for mode in ['match','missing','edited','local_drift']:
 with tempfile.TemporaryDirectory(prefix='draft-reconcile-') as directory:
  dbpath=Path(directory)/'fixture.db';remote=[];reads=[]
  def connect():return sqlite3.connect(dbpath,factory=ClosingConnection)
  with connect() as c:install(c)
  key=operation_key('william','fixture-message')
  request={'to':'fixture@example.invalid','subject':'Synthetic','body':'Synthetic unsent body','thread_id':'fixture-thread'}
  def create(raw,thread):
   with connect() as c:
    assert c.execute('SELECT state FROM email_action_intents WHERE operation_key=?',(key,)).fetchone()==('unconfirmed',)
    assert c.execute('SELECT COUNT(*) FROM email_draft_recovery_evidence WHERE operation_key=?',(key,)).fetchone()[0]==1
   remote.append({'id':'fixture-draft','message':{'raw':raw,'threadId':thread,'labelIds':['DRAFT']}})
   raise TimeoutError('fixture acceptance then lost acknowledgment')
  try:perform_recoverable_draft(connect,'william','fixture-message',request,create);assert False
  except OutcomeHeld:pass
  class Read:
   def __init__(self,method,kwargs):self.method=method;self.kwargs=kwargs
   def execute(self,num_retries):
    assert num_retries==0;reads.append(self.method)
    if self.method=='list':return {'drafts':[] if mode=='missing' else [{'id':'fixture-draft'}]}
    result=json.loads(json.dumps(remote[0]))
    if mode=='edited':
     data=base64.urlsafe_b64decode(result['message']['raw']);result['message']['raw']=base64.urlsafe_b64encode(data.replace(b'Synthetic unsent body',b'Owner edited content')).decode()
    if mode=='local_drift':
     with connect() as c:c.execute("UPDATE email_draft_recovery_evidence SET fingerprint=? WHERE operation_key=?",('b'*64,key));c.commit()
    return result
  class Gmail:
   def users(self):return self
   def drafts(self):return self
   def list(self,**kw):return Read('list',kw)
   def get(self,**kw):return Read('get',kw)
  result=reconcile_draft(connect,key,Gmail())
  with connect() as c:
   state=c.execute('SELECT state FROM email_action_intents').fetchone()[0]
   holds=c.execute('SELECT COUNT(*) FROM email_mailbox_admission').fetchone()[0]
  assert holds==(0 if mode=='match' else 1)
  assert state==('confirmed' if mode=='match' else 'unconfirmed') and len(remote)==1
  if mode=='match':
   receipt=perform_recoverable_draft(connect,'william','fixture-message',request,lambda *a:(_ for _ in ()).throw(AssertionError('Duplicate create')))
   assert receipt=={'draft_created':True,'id':'fixture-draft'}
  results.append({'case':mode,'state':state,'simulated_creates':len(remote),'read_calls':len(reads),'result':result['state'],'retained_mailbox_holds':holds})
print(json.dumps({'cases':results,'intent_and_marker_saved_before_callback':True,'actual_gmail_calls':0,'production_changes':False,'limits':'Synthetic Gmail; creation helper not yet wired to Harness; no live marker preservation or human-account credential proof'}))
