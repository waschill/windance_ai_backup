import json,subprocess
from types import SimpleNamespace
import receipt_report_transport as transport
from outbox_wire_protocol import envelope,CODES

payload={'to':'synthetic-owner','chunks':['synthetic private body'],'sms':False};key='synthetic-key'
cases=[]
for case in ('verified','pending','uncertain','legacy','wrong_identity','wrong_body','wrong_exit','missing_key','timeout','malformed'):
    calls=[]
    def run(command,**kwargs):
        calls.append(True)
        assert 'synthetic private body' not in ' '.join(command) and key not in ' '.join(command)
        assert json.loads(kwargs['input'])=={'key':key,'payload':payload}
        assert kwargs['timeout']==75
        if case=='timeout':raise subprocess.TimeoutExpired(command,75)
        result={'status':{'pending':'pending','uncertain':'uncertain','legacy':'legacy_submission'}.get(case,'verified_delivery')}
        if result['status']=='verified_delivery':result.update(independent_delivery_verified=True,chunks=1)
        value=envelope(key,payload,result);code=CODES[result['status']]
        if case=='wrong_identity':value['request_id']='different'
        if case=='wrong_body':value['content_sha256']='different'
        if case=='wrong_exit':code=14
        return SimpleNamespace(returncode=code,stdout='not json' if case=='malformed' else json.dumps(value))
    transport.subprocess=SimpleNamespace(run=run,TimeoutExpired=subprocess.TimeoutExpired)
    try:result=transport.send_report(payload['to'],payload['chunks'][0],'' if case=='missing_key' else key)
    except ValueError:
        assert case=='missing_key' and not calls
        result={'ok':False,'status':'missing_key'}
    assert result['ok'] is (case=='verified'),(case,result)
    if case!='missing_key':assert len(calls)==1
    cases.append({'case':case,'success':result['ok']})
print(json.dumps({'status':'passed','cases':cases,'real_ssh':0,'real_sends':0}))
