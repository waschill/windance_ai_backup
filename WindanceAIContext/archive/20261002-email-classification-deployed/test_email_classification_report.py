"""Actual report path with synthetic classifier, inbox, DB and mailbox adapters."""
import ast,datetime as dt,hashlib,json,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
path=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/Users/herald/backups/email-classification-candidate-20261002/agent_harness.candidate.private.py')
if len(sys.argv)>1:
 sys.path.insert(0,str(path.parent))
 import email_classification_contract
 assert Path(email_classification_contract.__file__).resolve()==path.parent/'email_classification_contract.py'
source=path.read_text();names={'gmail_autonomy_report','classify_email_autonomy','parse_email_autonomy_decisions'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==3
outcomes=[]
for mode in ['valid','cross_batch','duplicate']:
 with tempfile.TemporaryDirectory(prefix='email-report-contract-') as directory:
  dbpath=Path(directory)/'fixture.db';actions=[];saves=[];calls=[]
  def db():
   c=sqlite3.connect(dbpath);c.row_factory=sqlite3.Row;return c
  with db() as c:c.execute('CREATE TABLE email_autonomy_actions(run_id TEXT,ordinal INTEGER,message_id TEXT,thread_id TEXT,sender TEXT,subject TEXT,decision TEXT,action TEXT,reason TEXT,draft_id TEXT,created_at TEXT)')
  def row(i,decision='escalate'):return {'index':i,'decision':decision,'reason':'synthetic fixture','draft_intent':'synthetic draft'}
  def model(*args):
   batch=len(calls);calls.append(1)
   rows=[row(i) for i in range(1,9)] if batch==0 else [row(9)]
   if mode=='valid' and batch==0:rows[0]=row(1,'automatic');rows[1]=row(2,'draft')
   if mode=='duplicate' and batch==0:rows.append(row(1,'automatic'))
   if mode=='cross_batch' and batch==1:rows=[row(1,'automatic')]
   return json.dumps(rows),'fixture','fixture'
  items=[{'id':f'fixture-{i}','thread_id':f'thread-{i}','from':'fixture@example.invalid','subject':'synthetic'} for i in range(1,10)]
  def draft(*args):actions.append('draft');return {'id':'synthetic-unsent-draft'}
  ns={'Any':Any,'json':json,'re':re,'dt':dt,'uuid':uuid,'db':db,'now':lambda:'fixture-time',
      'require_william_mailbox':lambda:None,'recent_inbox_email':lambda **k:items,
      'apply_email_sender_rules':lambda x:(x,[]),'save_email_report_refs':lambda *a,**k:saves.append(k.get('ready',True)),
      'model_reply':model,'email_autonomy_risk_reason':lambda x:None,'short_sender':lambda x:'fixture',
      'compact_subject':lambda *a:'synthetic','sender_address':lambda x:'fixture@example.invalid',
      'compose_numbered_email_draft':lambda *a:'synthetic unsent body','gmail_create_draft':draft,
      'gmail_delete_message':lambda *a:actions.append('trash'),'audit':lambda *a:None}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-report>','exec'),ns)
  result=ns['gmail_autonomy_report']()
  assert saves==[False,True] and len(calls)==2
  with db() as c:rows=c.execute('SELECT decision,action FROM email_autonomy_actions').fetchall()
  assert len(rows)==9
  if mode=='valid':assert actions==['trash','draft']
  else:assert not actions and all(tuple(r)==('escalate','left_untouched') for r in rows)
  outcomes.append({'case':mode,'synthetic_mailbox_actions':actions,'recorded_items':len(rows),'report_published_after_processing':True})
print(json.dumps({'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':outcomes,'real_mailbox_actions':0,'actual_model_calls':0,'limits':'Synthetic risk/sender-rule/reference adapters; owner authentication, semantic classification and remote-outcome recovery not certified'}))
