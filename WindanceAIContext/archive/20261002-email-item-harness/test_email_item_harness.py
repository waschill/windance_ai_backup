"""Actual schema and batch executor with fake leaf effects and mixed outcomes."""
import ast,datetime as dt,hashlib,json,os,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-item-harness-r2-20261002');sys.path.insert(0,str(root))
from email_approved_item_intent import ItemHeld
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text();names={'db','ClosingConnection','seed_memories','execute_approved_action'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==4
results=[]
for mode in ['normal','second_lost','second_bad_receipt']:
 with tempfile.TemporaryDirectory() as folder:
  effects=[]
  def trash(message_id):
   effects.append(message_id)
   if message_id=='fixture-1' and mode=='second_lost':raise TimeoutError('PRIVATE_SENTINEL')
   return {'trashed':True,'id':'wrong' if message_id=='fixture-1' and mode=='second_bad_receipt' else message_id}
  ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'json':json,'now':lambda:'fixture','require_william_mailbox':lambda:None,'require_payload':lambda p,k:p[k],'gmail_delete_message':trash}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-item-executor>','exec'),ns)
  payload={'actions':[{'action':'gmail.delete','message_id':f'fixture-{i}'} for i in range(2)]}
  with ns['db']() as c:c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES('fixture','gmail.batch',?,'executing','fixture')",(json.dumps(payload),))
  for attempt in range(2):
   try:ns['execute_approved_action']('gmail.batch',payload,approval_id='fixture')
   except ItemHeld:assert mode!='normal'
   else:assert mode=='normal'
  assert effects==['fixture-0','fixture-1']
  with ns['db']() as c:
   states=[r[0] for r in c.execute('SELECT state FROM email_approved_item_intents ORDER BY root_item_index')]
   assert states==['confirmed','confirmed' if mode=='normal' else 'unconfirmed']
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  results.append({'case':mode,'synthetic_effects':len(effects),'item_states':states,'second_batch_attempt_repeated_effect':False})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Actual batch executor/schema, intercepted leaf primitives. Whole/selected handler composition and single actions/shared mailbox holds/full recovery remain.'}))
