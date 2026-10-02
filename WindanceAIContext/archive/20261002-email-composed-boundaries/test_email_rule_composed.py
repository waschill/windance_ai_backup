"""Actual schema/rule/report/Trash composition with synthetic remote state."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-trash-receipt-20261002');sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text()
names={'db','ClosingConnection','seed_memories','gmail_autonomy_report','apply_email_sender_rules','gmail_delete_message'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==6
results=[]
for mode in ['normal','mark_response_lost','trash_response_lost','local_tracking_failure']:
 with tempfile.TemporaryDirectory() as folder:
  calls=[];classifications=[];labels={'INBOX','UNREAD'};audits=[]
  item={'id':'fixture-message','from':'fixture@example.invalid','subject':'Synthetic','thread_id':'fixture-thread'}
  class Request:
   def __init__(self,method):self.method=method
   def execute(self,num_retries):
    assert num_retries==0;calls.append(self.method)
    if self.method=='mark':labels.discard('UNREAD')
    else:labels.discard('INBOX');labels.add('TRASH')
    if mode==self.method+'_response_lost':raise TimeoutError('PRIVATE_SENTINEL')
    return {'id':'fixture-message','labelIds':sorted(labels)}
  class Gmail:
   def users(self):return self
   def messages(self):return self
   def modify(self,**kw):return Request('mark')
   def trash(self,**kw):return Request('trash')
  def classify(items):classifications.append(len(items));return {}
  ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'now':lambda:'fixture',
  'require_william_mailbox':lambda:None,'gmail_service':lambda:Gmail(),
  'recent_inbox_email':lambda **k:[dict(item)],'save_email_report_refs':lambda *a,**kw:None,'classify_email_autonomy':classify,
  'email_autonomy_risk_reason':lambda x:None,'short_sender':lambda x:'fixture','compact_subject':lambda *a:'Synthetic',
  'sender_address':lambda x:'fixture@example.invalid','audit':lambda *a:audits.append(a),
  'email_sender_rules':lambda:{'fixture@example.invalid':{'action':'notify_delete'}},'note_sender_rule_match':lambda *a:None,'gmail_state':lambda x:'inbox','email_importance':lambda x:'normal'}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-composed-rule>','exec'),ns)
  with ns['db']() as c:
   if mode=='local_tracking_failure':c.execute("CREATE TRIGGER fail_tracking BEFORE INSERT ON max_email_tracking BEGIN SELECT RAISE(ABORT,'fixture'); END")
  report=ns['gmail_autonomy_report']()[0]
  before=list(calls)
  if mode=='local_tracking_failure':
   with ns['db']() as c:c.execute('DROP TRIGGER fail_tracking')
  # Represents stale listing or a separately invoked sender-rule sweep.
  kept,notices=ns['apply_email_sender_rules']([dict(item)])
  assert calls==before and not classifications
  assert calls==(['mark'] if mode=='mark_response_lost' else ['mark','trash'])
  with ns['db']() as c:
   state=c.execute('SELECT state FROM email_action_intents').fetchone()[0]
   tracked=c.execute('SELECT COUNT(*) FROM max_email_tracking').fetchone()[0]
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  uncertain=mode in {'mark_response_lost','trash_response_lost'}
  assert state==('unconfirmed' if uncertain else 'confirmed')
  assert tracked==(0 if uncertain else 1)
  if uncertain:assert kept and '1 previously attempted mailbox operation(s) remain unconfirmed' in report
  else:assert not kept
  assert 'PRIVATE_SENTINEL' not in report+repr(audits)+repr(notices)
  results.append({'case':mode,'remote_calls':calls,'later_rule_repeated_remote_call':False,'classifier_calls':0,'intent_state':state,'tracking_rows':tracked,'partial_mark_read_only':mode=='mark_response_lost'})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Synthetic remote; stale listing intentional. Confirmed rule retry can repeat local notes. Direct approved actions, undo, transport and account identity remain outside coverage.'}))
