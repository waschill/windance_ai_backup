"""Synthetic account policy and profile checks; never reads actual account config."""
import json,tempfile
from pathlib import Path
from gmail_account_boundary_r2 import expected_account,verify,AccountUnverified
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'policy.json';invalid=0
    for value in (None,'bad-json',json.dumps({}),json.dumps({'expected_email':'bad'}),json.dumps({'expected_email':'a@example.invalid','extra':True}),'x'*4097):
        if value is None:
            if path.exists():path.unlink()
        else:path.write_text(value)
        try:expected_account(path);raise AssertionError('Bad policy accepted')
        except AccountUnverified:invalid+=1
    path.write_text(json.dumps({'expected_email':'Owner@Example.invalid'}));expected=expected_account(path)
    class Service:
        def __init__(self,profile):self.profile=profile;self.calls=0
        def users(self):return self
        def getProfile(self,**kwargs):assert kwargs=={'userId':'me'};return self
        def execute(self,**kwargs):
            assert kwargs=={'num_retries':0};self.calls+=1
            if isinstance(self.profile,Exception):raise self.profile
            return self.profile
    good=Service({'emailAddress':'OWNER@example.invalid'});assert verify(good,expected) is good and good.calls==1
    refused=0
    for profile in ({'emailAddress':'other@example.invalid'},{},[],{'emailAddress':None},RuntimeError('PRIVATE_SENTINEL')):
        service=Service(profile)
        try:verify(service,expected);raise AssertionError('Unverified account accepted')
        except AccountUnverified as exc:assert 'PRIVATE_SENTINEL' not in str(exc);refused+=1
        assert service.calls==1
print(json.dumps({'bad_policy_cases':invalid,'profile_refusal_cases':refused,'casefold_match_pass':True,'retry_disabled':True,'real_account_access':False}))

