"""Actual numbered-rule command/schema; retry and later-report identity."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-direct-rule-intent-20261002');sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text();names={'db','ClosingConnection','seed_memories','prepare_gmail_report_reply_actions','numbers_after_keywords'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==len(names)
results=[]
for phrase in ['always delete 1','notify delete 1']:
 for mode in ['normal','lost']:
  with tempfile.TemporaryDirectory() as folder:
   effects=[];rules=[];report=['first']
   def trash(mid):
    effects.append(mid)
    if mode=='lost':raise TimeoutError('PRIVATE_SENTINEL')
    return {'trashed':True,'id':mid}
   ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'json':json,'now':lambda:'fixture','require_william_mailbox':lambda:None,
   'latest_email_ref_map':lambda:{1:{'report_key':report[0],'message_id':'fixture-message','sender':'fixture@example.invalid','subject':'Synthetic'}},'short_sender':lambda x:'fixture','compact_subject':lambda *a:'Synthetic','upsert_email_sender_rule':lambda *a:(rules.append(1) or 'fixture@example.invalid'),'gmail_delete_message':trash,'consume_latest_email_ref_map':lambda:None}
   exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-direct-rule>','exec'),ns)
   responses=[ns['prepare_gmail_report_reply_actions'](phrase),ns['prepare_gmail_report_reply_actions'](phrase)]
   assert len(effects)==1 and 'PRIVATE_SENTINEL' not in repr(responses)
   report[0]='later';responses.append(ns['prepare_gmail_report_reply_actions'](phrase))
   assert len(effects)==(2 if mode=='normal' else 1)
   if mode=='lost':assert len(rules)==1
   results.append({'command':phrase,'outcome':mode,'synthetic_effects':len(effects),'same_report_repeated_effect':False,'new_report_allowed_only_after_confirmed':True})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Source refs/owner/rule storage and Trash primitive intercepted. Local sender-rule transaction atomicity, reference consumption and full request transport remain unverified.'}))
