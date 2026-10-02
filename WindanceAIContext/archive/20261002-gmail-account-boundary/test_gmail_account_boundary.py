import json
from gmail_account_boundary import verify,MailboxIdentityError
out=[]
for mode in ['match','case_match','wrong_account','missing_expected','invalid_expected','missing_profile','profile_error']:
 calls=[]
 class Service:
  def users(self):return self
  def getProfile(self,**kw):assert kw=={'userId':'me'};return self
  def execute(self,num_retries):
   assert num_retries==0;calls.append('profile')
   if mode=='profile_error':raise RuntimeError('fixture private provider error')
   if mode=='missing_profile':return {}
   return {'emailAddress':'other@example.invalid' if mode=='wrong_account' else 'fixture@example.invalid'}
 service=Service();expected={'case_match':'Fixture@Example.Invalid','missing_expected':None,'invalid_expected':' fixture@example.invalid'}.get(mode,'fixture@example.invalid')
 try:assert verify(service,expected) is service;allowed=True
 except MailboxIdentityError as e:allowed=False;assert 'fixture private provider error' not in str(e) and 'other@example.invalid' not in str(e)
 assert allowed==(mode in ['match','case_match'])
 if mode in ['missing_expected','invalid_expected']:assert not calls
 out.append({'case':mode,'allowed':allowed,'profile_reads':len(calls)})
print(json.dumps({'cases':out,'actual_gmail_calls':0,'production_changes':False,'limits':'Requires independently configured expected owner account; human identity and intake authorization are separate gates'}))
