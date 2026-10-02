"""Actual approval handlers through actual executor/Trash and journals."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-item-harness-r2-20261002');sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text()
names={'db','ClosingConnection','seed_memories','execute_approved_action','approve_pending','find_pending_approval','latest_pending_approval','process_numbered_gmail_pin_decisions','gmail_delete_message'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==len(names)
results=[]
for mode in ['whole_normal','whole_last_lost','selected_normal','selected_last_lost']:
 with tempfile.TemporaryDirectory() as folder:
  calls=[];audits=[];remote={f'fixture-{i}':{'INBOX','UNREAD'} for i in range(3)}
  class Request:
   def __init__(self,method,args):self.method=method;self.args=args
   def execute(self,num_retries):
    assert num_retries==0;mid=self.args['id'];calls.append((mid,self.method))
    if self.method=='mark':remote[mid].discard('UNREAD')
    else:remote[mid].discard('INBOX');remote[mid].add('TRASH')
    if mode.endswith('last_lost') and mid=='fixture-2' and self.method=='trash':raise TimeoutError('PRIVATE_SENTINEL')
    return {'id':mid,'labelIds':sorted(remote[mid])}
  class Gmail:
   def users(self):return self
   def messages(self):return self
   def modify(self,**kw):return Request('mark',kw)
   def trash(self,**kw):return Request('trash',kw)
  ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'json':json,'now':lambda:'later-fixture',
  'require_william_mailbox':lambda:None,'latest_email_ref_map':lambda:{i+1:{'message_id':f'fixture-{i}'} for i in range(3)},'auth_word_matches':lambda text:True,'approval_is_fresh':lambda a:True,'require_payload':lambda p,k:p[k],'gmail_service':lambda:Gmail(),'audit':lambda *a:audits.append(a)}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<full-approval-chain>','exec'),ns)
  payload={'actions':[{'action':'gmail.delete','message_id':f'fixture-{i}'} for i in range(3)],'_expires_at':'fixture-expiry'}
  with ns['db']() as c:c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES('root-fixture','gmail.batch',?,'pending','fixture-time')",(json.dumps(payload),))
  def invoke():return ns['approve_pending']('root-fixture') if mode.startswith('whole') else ns['process_numbered_gmail_pin_decisions']('number 1 approved; number 3 approved')
  response=invoke();before=list(calls);retry=invoke()
  assert calls==before and 'PRIVATE_SENTINEL' not in repr(response)+repr(retry)+repr(audits)
  selected=[0,1,2] if mode.startswith('whole') else [0,2]
  assert calls==[(f'fixture-{i}',step) for i in selected for step in ['mark','trash']]
  with ns['db']() as c:
   status=c.execute("SELECT status FROM approvals WHERE id='root-fixture'").fetchone()[0]
   items=[tuple(r) for r in c.execute('SELECT root_item_index,state FROM email_approved_item_intents ORDER BY root_item_index')]
   children=c.execute("SELECT payload_json FROM approvals WHERE id!='root-fixture'").fetchall()
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert status==('uncertain' if mode.endswith('last_lost') else 'executed')
  assert items==[(i,'unconfirmed' if i==2 and mode.endswith('last_lost') else 'confirmed') for i in selected]
  assert len(children)==(0 if mode.startswith('whole') else 1)
  if children:assert json.loads(children[0][0])['actions']==[payload['actions'][1]]
  if mode.endswith('last_lost'):assert 'unconfirmed' in response[0]
  results.append({'case':mode,'parent_status':status,'item_states':items,'simulated_remote_calls':len(calls),'repeat_approval_added_calls':False,'remaining_approvals':len(children)})
print(json.dumps({'candidate_files_sha256':manifest,'cases':results,'actual_gmail_calls':0,'actual_sends':0,'production_changes':False,'limits':'Actual handlers/executor/journals/Trash; auth/freshness/source refs mocked and Gmail simulated. Live identities, other primitive actions, shared holds, recovery and operator visibility remain.'}))
