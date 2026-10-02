"""Actual single approval, executor and journal; intercepted mailbox primitive."""
import ast,datetime as dt,hashlib,json,os,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-single-intent-20261002');sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text();names={'db','ClosingConnection','seed_memories','execute_approved_action','approve_pending','find_pending_approval'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==len(names)
results=[]
for mode in ['normal','lost_response','bad_receipt']:
 with tempfile.TemporaryDirectory() as folder:
  effects=[];audits=[]
  def trash(mid):
   effects.append(mid)
   if mode=='lost_response':raise TimeoutError('PRIVATE_SENTINEL')
   return {'trashed':True,'id':'wrong' if mode=='bad_receipt' else mid}
  ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'json':json,'now':lambda:'fixture','require_william_mailbox':lambda:None,'require_payload':lambda p,k:p[k],'gmail_delete_message':trash,'approval_is_fresh':lambda a:True,'audit':lambda *a:audits.append(a)}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<single-approved-item>','exec'),ns)
  with ns['db']() as c:c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES('fixture','gmail.delete',?,'pending','fixture')",(json.dumps({'message_id':'fixture-message'}),))
  responses=[ns['approve_pending']('fixture'),ns['approve_pending']('fixture')]
  assert effects==['fixture-message'] and 'PRIVATE_SENTINEL' not in repr(responses)+repr(audits)
  with ns['db']() as c:
   state=c.execute('SELECT status FROM approvals').fetchone()[0]
   receipt=tuple(c.execute('SELECT root_approval_id,root_item_index,state FROM email_approved_item_intents').fetchone())
  assert state==('executed' if mode=='normal' else 'uncertain')
  assert receipt==('fixture',0,'confirmed' if mode=='normal' else 'unconfirmed')
  results.append({'case':mode,'synthetic_effects':len(effects),'approval_status':state,'item_status':receipt[2]})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Single Trash integration only, primitive intercepted. Other single actions/shared admission/account binding/recovery/operator reconciliation remain.'}))
