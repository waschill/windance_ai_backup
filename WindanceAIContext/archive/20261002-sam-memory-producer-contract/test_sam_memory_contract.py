"""Admission only; synthetic schedule, no service/DB/Odoo operation."""
import json,secrets
from sam_memory_contract import admit,ProducerDenied
token=secrets.token_urlsafe(32)
payload={'kind':'sam_daily_schedule','key':'2026-10-01','value':'Synthetic daily totals: completed 1',
         'confidence':0.92,'source':'SAM schedule display'}
calls=[]
def content(value):calls.append(value);return 'PRIVATE_SENTINEL' not in value
accepted=admit('Bearer '+token,token,payload,content)
assert accepted['producer']=='sam' and accepted['scope']=='business' and accepted['human_owner'] is None
assert accepted['independently_verified'] is False
cases=[('missing_auth',None,payload),('wrong_auth','Bearer invalid',payload),
 ('personal_kind','Bearer '+token,{**payload,'kind':'preference'}),
 ('owner_override','Bearer '+token,{**payload,'owner':'william'}),
 ('invalid_date','Bearer '+token,{**payload,'key':'2026-02-30'}),
 ('noncanonical_date','Bearer '+token,{**payload,'key':'20261001'}),
 ('source_override','Bearer '+token,{**payload,'source':'William'}),
 ('boolean_confidence','Bearer '+token,{**payload,'confidence':True}),
 ('oversize','Bearer '+token,{**payload,'value':'x'*65537}),
 ('secret_fixture','Bearer '+token,{**payload,'value':'PRIVATE_SENTINEL'})]
for name,auth,body in cases:
    before=len(calls)
    try:admit(auth,token,body,content)
    except ProducerDenied as exc:assert 'PRIVATE_SENTINEL' not in str(exc)
    else:raise AssertionError(name)
    if name in ('missing_auth','wrong_auth'):assert len(calls)==before
print(json.dumps({'valid_business_shape_accepted':True,'denied_cases':[x[0] for x in cases],
                  'human_owner_not_inferred':True,'storage_calls':0,'production_changes':False}))
