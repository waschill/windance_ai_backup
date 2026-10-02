"""Actual five Gmail helpers, fake responses and no real send capability."""
import ast,base64,hashlib,json,sys
from email.message import EmailMessage
from pathlib import Path
from typing import Any
root=Path(sys.argv[1]);sys.path.insert(0,str(root));source=root/'agent_harness.candidate.private.py'
fixed='email-action-receipts-' in str(root);tree=ast.parse(source.read_text());results=[]
for name in ['gmail_mark_read','gmail_archive','gmail_create_draft','gmail_send_message','gmail_send_draft']:
 node=next(n for n in tree.body if getattr(n,'name','')==name)
 modes=['valid','missing_id','blank_id']+(['wrong_id','wrong_labels'] if name in {'gmail_mark_read','gmail_archive'} else [])
 for mode in modes:
  calls=[];audits=[];response={'id':'fixture','labelIds':[]}
  if mode=='missing_id':response.pop('id')
  if mode=='blank_id':response['id']=' '
  if mode=='wrong_id':response['id']='other'
  if mode=='wrong_labels':response['labelIds']=['UNREAD','INBOX']
  class Gmail:
   def users(self):return self
   def messages(self):return self
   def drafts(self):return self
   def modify(self,**kw):return self
   def create(self,**kw):return self
   def send(self,**kw):return self
   def execute(self,**kw):
    calls.append(1)
    if fixed:assert kw=={'num_retries':0}
    return response
  ns={'Any':Any,'EmailMessage':EmailMessage,'base64':base64,'gmail_service':lambda:Gmail(),'audit':lambda *a:audits.append(a)}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-gmail-helper>','exec'),ns)
  args=('fixture',) if name in {'gmail_mark_read','gmail_archive','gmail_send_draft'} else ('fixture@example.invalid','Synthetic','Unsent synthetic body')
  error=None
  try:ns[name](*args)
  except RuntimeError as exc:error=str(exc)
  assert len(calls)==1
  if fixed and mode!='valid':assert error and not audits
  else:assert error is None and len(audits)==1
  results.append({'helper':name,'case':mode,'success_reported':error is None})
print(json.dumps({'fixed':fixed,'candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':results,'actual_gmail_calls':0,'actual_sends':0,'production_changes':False,'limits':'Synthetic provider acknowledgments; nonempty send receipt means acceptance evidence, not delivery. Full action-journal integration and live compatibility remain.'}))
