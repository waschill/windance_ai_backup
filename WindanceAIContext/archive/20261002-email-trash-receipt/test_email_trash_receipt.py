"""Actual helper only; synthetic receipts and side effects, no Gmail connection."""
import ast,hashlib,json,sys
from pathlib import Path
from typing import Any
root=Path(sys.argv[1]);p=root/'agent_harness.candidate.private.py';s=p.read_text()
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='gmail_delete_message')
fixed='email-trash-receipt-' in str(root);results=[]
for mode in ['normal','mark_lost','mark_wrong_id','mark_missing_labels','mark_still_unread','trash_wrong_id','trash_missing_label','trash_lost']:
 calls=[];audits=[]
 class Request:
  def __init__(self,method):self.method=method
  def execute(self,**kw):
   calls.append(self.method)
   if fixed:assert kw=={'num_retries':0}
   if mode==self.method+'_lost':raise TimeoutError('PRIVATE_SENTINEL')
   if self.method=='mark':return {'id':'wrong' if mode=='mark_wrong_id' else 'fixture',**({} if mode=='mark_missing_labels' else {'labelIds':['UNREAD'] if mode=='mark_still_unread' else ['INBOX']})}
   return {'id':'wrong' if mode=='trash_wrong_id' else 'fixture','labelIds':[] if mode=='trash_missing_label' else ['TRASH']}
 class Gmail:
  def users(self):return self
  def messages(self):return self
  def modify(self,**kw):assert kw=={'userId':'me','id':'fixture','body':{'removeLabelIds':['UNREAD']}};return Request('mark')
  def trash(self,**kw):assert kw=={'userId':'me','id':'fixture'};return Request('trash')
 ns={'Any':Any,'gmail_service':lambda:Gmail(),'audit':lambda *a:audits.append(a)}
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-trash>','exec'),ns)
 error=None;result=None
 try:result=ns['gmail_delete_message']('fixture')
 except Exception as exc:error=str(exc)
 if fixed:
  if mode=='normal':assert result=={'trashed':True,'marked_read':True,'id':'fixture'}
  else:assert result is None and error=='Mailbox change outcome unconfirmed; reconcile before retrying'
  if mode.startswith('mark_'):assert calls==['mark']
  assert 'PRIVATE_SENTINEL' not in repr(audits)+str(error)
 else:
  if mode!='trash_lost':assert result and result['trashed'] is True
  assert calls==['mark','trash']
 results.append({'case':mode,'reported_success':bool(result),'calls':calls})
print(json.dumps({'fixed':fixed,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cases':results,'actual_mailbox_calls':0,'production_changes':False}))
