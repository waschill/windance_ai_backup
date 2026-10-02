"""Unchanged profile main with synthetic config, OAuth resolver and SDK (no network)."""
import importlib.util,json,os,sys,tempfile,types
from pathlib import Path
from types import SimpleNamespace
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
import email_inline_inference as adapter
spec=importlib.util.spec_from_file_location('profile_inference',stage/'profile_inference.py')
profile=importlib.util.module_from_spec(spec);sys.modules[spec.name]=profile;spec.loader.exec_module(profile)
def module(name,**values):
    m=types.ModuleType(name);m.__dict__.update(values);sys.modules[name]=m;return m
for name in ('agent','hermes_cli'):module(name,__path__=[])
module('yaml',safe_load=json.loads)
calls=[];closed=[];mode='ok'
def resolve(**kwargs):
    assert kwargs=={'requested':'openai-codex','target_model':'gpt-5.6-terra'}
    return {'provider':'wrong' if mode=='bad_provider' else 'openai-codex','api_key':'synthetic','base_url':'https://fixture.invalid'}
def create(**kwargs):
    calls.append(kwargs)
    assert kwargs['model']=='gpt-5.6-terra' and kwargs['max_tokens']==1800 and kwargs['timeout']==75
    assert 'fixture identity' in kwargs['messages'][0]['content']
    if mode=='sdk_error':raise RuntimeError('PRIVATE_SENTINEL')
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='' if mode=='empty' else 'fixture reply'))])
class Client:
    def __init__(self,**kwargs):
        assert kwargs['max_retries']==0 and kwargs['api_key']=='synthetic'
        self.chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    def close(self):closed.append(1)
module('openai',OpenAI=Client)
module('hermes_cli.runtime_provider',resolve_runtime_provider=resolve)
module('agent.auxiliary_client',CodexAuxiliaryClient=lambda client,model:client)
module('agent.codex_headers',apply_required_codex_headers=lambda *a,**k:None)
results=[];streams=(sys.stdin,sys.stdout,sys.stderr)
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);account=root/'herald';account.mkdir();(account/'PUBLIC_IDENTITY.md').write_text('fixture identity')
    profile.Path=lambda value:root if value=='/Users/herald/.hermes/profiles' else Path(value)
    for mode in ('ok','bad_config_route','bad_provider','empty','sdk_error'):
        (account/'config.yaml').write_text(json.dumps({'model':{'provider':'openai-codex','default':'wrong' if mode=='bad_config_route' else 'gpt-5.6-terra'}}))
        audits=[];h=SimpleNamespace(audit=lambda *a:audits.append(a));adapter.bind(h)
        before=len(calls);result=h.model_reply('fixture system','fixture user','[]')
        assert result==(('fixture reply','openai-codex','gpt-5.6-terra') if mode=='ok' else ('[]','openai-codex-unavailable','gpt-5.6-terra'))
        assert streams==(sys.stdin,sys.stdout,sys.stderr) and 'PRIVATE_SENTINEL' not in json.dumps(audits)
        results.append({'case':mode,'synthetic_sdk_calls':len(calls)-before,'fallback':mode!='ok'})
assert len(closed)==3
print(json.dumps({'cases':results,'actual_profile_main':True,'client_cleanup':True,'fixed_oauth_terra_route':True,
    'real_model_or_credential_calls':0,'limits':'Resolver and SDK are synthetic; actual OAuth resolution/provider dependencies remain unverified.'}))
