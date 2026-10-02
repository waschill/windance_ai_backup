"""Actual DB/report/prepared-Gmail helper with fake remote, then reconciliation."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-recoverable-candidate-20261002');sys.path.insert(0,str(root))
from email_action_intent import operation_key,reconcile_draft
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text();names={'db','ClosingConnection','seed_memories','gmail_autonomy_report','_gmail_create_prepared_draft'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==5
results=[]
for mode in ['normal','lost_response']:
 with tempfile.TemporaryDirectory(prefix='harness-recoverable-') as folder:
  remote=[];calls=[];ns={};key=operation_key('william','fixture-message')
  class Request:
   def __init__(self,method,args):self.method=method;self.args=args
   def execute(self,num_retries):
    assert num_retries==0;calls.append(self.method)
    if self.method=='create':
     with ns['db']() as c:
      assert c.execute('SELECT state FROM email_action_intents WHERE operation_key=?',(key,)).fetchone()[0]=='unconfirmed'
      assert c.execute('SELECT COUNT(*) FROM email_draft_recovery_evidence WHERE operation_key=?',(key,)).fetchone()[0]==1
     data=self.args['body']['message'];remote.append({'id':'fixture-draft','message':{**data,'labelIds':['DRAFT']}})
     if mode=='lost_response':raise TimeoutError('synthetic accepted lost response')
     return remote[-1]
    if self.method=='list':return {'drafts':[{'id':'fixture-draft'}]}
    if self.method=='get':return remote[0]
    raise AssertionError('Unexpected API method')
  class Gmail:
   def users(self):return self
   def drafts(self):return self
   def create(self,**kw):return Request('create',kw)
   def list(self,**kw):return Request('list',kw)
   def get(self,**kw):return Request('get',kw)
  def forbidden(*a,**k):raise AssertionError('Legacy draft or real effect forbidden')
  ns.update({'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'now':lambda:'fixture',
   'require_william_mailbox':lambda:None,'gmail_service':lambda:Gmail(),'gmail_create_draft':forbidden,'gmail_delete_message':forbidden,
   'recent_inbox_email':lambda **k:[{'id':'fixture-message','from':'fixture@example.invalid','subject':'Synthetic','thread_id':'fixture-thread'}],
   'apply_email_sender_rules':lambda x:(x,[]),'save_email_report_refs':lambda *a,**k:None,
   'classify_email_autonomy':lambda x:{1:{'decision':'draft','reason':'fixture','draft_intent':'fixture'}},
   'email_autonomy_risk_reason':lambda x:None,'short_sender':lambda x:'fixture','compact_subject':lambda *a:'Synthetic',
   'sender_address':lambda x:'fixture@example.invalid','compose_numbered_email_draft':lambda *a:'Synthetic unsent body','audit':lambda *a:None})
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-harness-draft>','exec'),ns)
  ns['gmail_autonomy_report']()
  with ns['db']() as c:before=c.execute('SELECT state FROM email_action_intents').fetchone()[0]
  assert before==('confirmed' if mode=='normal' else 'unconfirmed')
  if mode=='lost_response':assert reconcile_draft(ns['db'],key,Gmail())['state']=='confirmed'
  ns['gmail_autonomy_report']()
  assert len(remote)==1 and calls.count('create')==1
  with ns['db']() as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  results.append({'case':mode,'prepared_mime_submissions':calls.count('create'),'recovery_reads':len(calls)-1,'repeat_create':False,'journal_confirmed':True})
print(json.dumps({'cases':results,'candidate_files_sha256':manifest,'actual_harness_db_report_and_draft_helper':True,'actual_gmail_calls':0,'production_changes':False,'limits':'Fake remote; account binding and Gmail marker preservation not live-proven; old action-row reconciliation and cross-path admission remain'}))
