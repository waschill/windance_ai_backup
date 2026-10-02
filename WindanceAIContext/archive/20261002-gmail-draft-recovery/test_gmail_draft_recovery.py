"""Fake Gmail read adapter; any write method is absent and would fail."""
import copy,json
from gmail_draft_recovery import prepare,inspect
key='a'*64;expected=prepare(key,'fixture@example.invalid','Synthetic','Synthetic unsent body')
out=[]
for scenario in ['match','missing','duplicate','paginated','changed_content','wrong_marker','wrong_draft_id','not_draft','wrong_thread','lookup_error']:
 calls=[]
 class Request:
  def __init__(self,kind,kwargs):self.kind=kind;self.kwargs=kwargs
  def execute(self,num_retries):
   assert num_retries==0;calls.append(self.kind)
   if scenario=='lookup_error':raise TimeoutError('fixture private exception')
   if self.kind=='list':
    assert self.kwargs=={'userId':'me','q':'rfc822msgid:'+expected['marker'],'maxResults':2,'includeSpamTrash':True}
    if scenario=='missing':return {'drafts':[]}
    if scenario=='duplicate':return {'drafts':[{'id':'one'},{'id':'two'}]}
    if scenario=='paginated':return {'drafts':[{'id':'one'}],'nextPageToken':'fixture'}
    return {'drafts':[{'id':'one'}]}
   assert self.kwargs=={'userId':'me','id':'one','format':'raw'}
   raw=expected['raw']
   if scenario=='changed_content':raw=prepare(key,'fixture@example.invalid','Synthetic','Different body')['raw']
   if scenario=='wrong_marker':raw=prepare('b'*64,'fixture@example.invalid','Synthetic','Synthetic unsent body')['raw']
   return {'id':'other' if scenario=='wrong_draft_id' else 'one','message':{'raw':raw,'labelIds':['SENT'] if scenario=='not_draft' else ['DRAFT'],'threadId':'other' if scenario=='wrong_thread' else 'thread'}}
 class Service:
  def users(self):return self
  def drafts(self):return self
  def list(self,**kwargs):return Request('list',kwargs)
  def get(self,**kwargs):return Request('get',kwargs)
 result=inspect(Service(),key,expected['fingerprint'],'thread')
 assert result['state']==('matched' if scenario=='match' else 'held') and len(calls)<=2
 if scenario=='match':assert result['write_permitted'] is False
 out.append({'case':scenario,'state':result['state'],'read_calls':len(calls)})
print(json.dumps({'cases':out,'maximum_read_calls':2,'writes_exposed':False,'actual_gmail_calls':0,'production_changes':False,'limits':'Marker preservation and Gmail indexing not live-verified; not wired to journal or production creation; no negative-result release'}))
