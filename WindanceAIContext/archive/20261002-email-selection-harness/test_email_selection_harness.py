"""Actual schema/selected-number handler with intercepted execution only."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,threading,uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-selection-harness-20261002');sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text()
names={'db','ClosingConnection','seed_memories','process_numbered_gmail_pin_decisions'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==4
results=[]
for mode in ['overlap','lost_response','wrong_pin','missing_reference','reject_only']:
 with tempfile.TemporaryDirectory() as folder:
  calls=[];audits=[];barrier=threading.Barrier(2);ns={}
  def latest(action):
   with ns['db']() as c:r=c.execute("SELECT * FROM approvals WHERE id='fixture' AND status='pending'").fetchone()
   if mode=='overlap':barrier.wait(timeout=5)
   return dict(r) if r else None
  def execute(action,payload):
   calls.append(payload['actions']);assert len(payload['actions'])==1 and payload['actions'][0]['message_id']=='fixture-0'
   if mode=='lost_response':raise TimeoutError('PRIVATE_SENTINEL')
   return {'ok':True}
  ns.update({'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'json':json,'now':lambda:'later-fixture',
  'require_william_mailbox':lambda:None,'latest_email_ref_map':lambda:{i+1:{'message_id':f'fixture-{i}'} for i in range(3) if not(mode=='missing_reference' and i==0)},'auth_word_matches':lambda text:mode!='wrong_pin','latest_pending_approval':latest,'approval_is_fresh':lambda a:True,'execute_approved_action':execute,'audit':lambda *a:audits.append(a)})
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-selected-handler>','exec'),ns)
  with ns['db']() as c:c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES('fixture','gmail.batch',?,'pending','fixture-time')",(json.dumps({'actions':[{'action':'gmail.delete','message_id':f'fixture-{i}'} for i in range(3)],'_expires_at':'fixture-expiry'}),))
  text='number 1 no approval' if mode=='reject_only' else 'number 1 approved; number 2 no approval'
  if mode=='overlap':
   with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:ns['process_numbered_gmail_pin_decisions'](text),range(2)))
  else:responses=[ns['process_numbered_gmail_pin_decisions'](text)]
  assert len(calls)==(1 if mode in {'overlap','lost_response'} else 0)
  assert 'PRIVATE_SENTINEL' not in repr(responses)+repr(audits)
  with ns['db']() as c:
   status=c.execute("SELECT status FROM approvals WHERE id='fixture'").fetchone()[0]
   children=c.execute("SELECT payload_json,requested_at FROM approvals WHERE id!='fixture'").fetchall()
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert status=={'overlap':'executed','lost_response':'uncertain','wrong_pin':'pending','missing_reference':'pending','reject_only':'rejected'}[mode]
  assert len(children)==(0 if mode in {'wrong_pin','missing_reference'} else 1)
  if children:assert children[0][1]=='fixture-time' and json.loads(children[0][0])['_expires_at']=='fixture-expiry'
  results.append({'case':mode,'intercepted_batch_executions':len(calls),'parent_status':status,'remaining_approvals':len(children)})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'PIN matcher and executor mocked; actual parser/reference checks/schema/claim exercised. End-to-end authentication, item outcomes, operator display and full startup/recovery remain.'}))
