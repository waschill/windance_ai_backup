"""Actual undo handler/schema/primitive chain with synthetic remote receipts."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-undo-harness-20261002');sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text();names={'db','ClosingConnection','seed_memories','undo_email_autonomy_action','gmail_unarchive','gmail_untrash_to_inbox','gmail_delete_draft'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==len(names)
results=[]
for action in ['archived','trashed','draft_created']:
 for outcome in ['normal','lost','bad_receipt']:
  with tempfile.TemporaryDirectory() as folder:
   calls=[]
   class Request:
    def __init__(self,method):self.method=method
    def execute(self,num_retries):
     assert num_retries==0;calls.append(self.method)
     if outcome=='lost':raise TimeoutError('PRIVATE_SENTINEL')
     if outcome=='bad_receipt':return {'id':'wrong','labelIds':['TRASH']}
     return {} if self.method=='delete' else {'id':'message','labelIds':['INBOX']}
   class Gmail:
    def users(self):return self
    def messages(self):return self
    def drafts(self):return self
    def modify(self,**kw):return Request('modify')
    def untrash(self,**kw):return Request('untrash')
    def delete(self,**kw):return Request('delete')
   ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'json':json,'now':lambda:'fixture','require_william_mailbox':lambda:None,'latest_email_ref_map':lambda:{1:{'report_key':'run','message_id':'message'}},'gmail_service':lambda:Gmail(),'audit':lambda *a:None}
   exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-undo-chain>','exec'),ns)
   with ns['db']() as c:c.execute("INSERT INTO email_autonomy_actions(run_id,ordinal,message_id,decision,action,reason,draft_id,created_at) VALUES('run',1,'message','fixture',?,'fixture','draft','fixture')",(action,))
   response=ns['undo_email_autonomy_action']('undo email 1');first=list(calls);again=ns['undo_email_autonomy_action']('undo email 1')
   assert calls==first and 'PRIVATE_SENTINEL' not in repr(response)+repr(again)
   with ns['db']() as c:
    state=c.execute('SELECT state FROM email_undo_intents').fetchone()[0];reversed_at=c.execute('SELECT reversed_at FROM email_autonomy_actions').fetchone()[0];holds=c.execute('SELECT COUNT(*) FROM email_mailbox_admission').fetchone()[0]
   assert state==('confirmed' if outcome=='normal' else 'unconfirmed') and bool(reversed_at)==(outcome=='normal') and holds==(0 if outcome=='normal' else 1)
   assert len(calls)==(2 if action=='trashed' and outcome=='normal' else 1)
   results.append({'action':action,'outcome':outcome,'synthetic_calls':len(calls),'repeat_added_calls':False,'state':state})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Synthetic Gmail and owner/reference adapters. Full auth, live provider compatibility, undo races/crashes and exact-package recovery remain.'}))
