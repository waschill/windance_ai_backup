"""Contract/std-stream tests with synthetic inference module; no model or OAuth access."""
import io,json,sys
from types import SimpleNamespace
import email_inline_inference as adapter
original=sys.modules.get('profile_inference');streams=(sys.stdin,sys.stdout,sys.stderr)
cases=[]
try:
 for mode in ('ok','wrong_route','empty','malformed','raised','oversize'):
    def main():
        wire=sys.stdout;sys.stdout=sys.stderr
        request=json.load(sys.stdin);assert request=={'system':'fixture-system','user':'fixture-user','profile':'herald','route':'profile'}
        if mode=='raised':raise RuntimeError('PRIVATE_SENTINEL')
        if mode=='malformed':wire.write('not-json');return
        if mode=='oversize':wire.write('x'*(1024*1024+1));return
        wire.write(json.dumps({'reply':'' if mode=='empty' else 'fixture-reply','provider':'wrong' if mode=='wrong_route' else 'openai-codex','model':'gpt-5.6-terra'}))
    sys.modules['profile_inference']=SimpleNamespace(main=main)
    audits=[];h=SimpleNamespace(audit=lambda *x:audits.append(x));adapter.bind(h)
    result=h.model_reply('fixture-system','fixture-user','[]')
    assert result==(('fixture-reply','openai-codex','gpt-5.6-terra') if mode=='ok' else ('[]','openai-codex-unavailable','gpt-5.6-terra'))
    assert 'PRIVATE_SENTINEL' not in json.dumps(audits)
    assert streams==(sys.stdin,sys.stdout,sys.stderr)
    cases.append(mode)
finally:
 if original is None:sys.modules.pop('profile_inference',None)
 else:sys.modules['profile_inference']=original
print(json.dumps({'cases':cases,'fixed_profile_and_route':True,'streams_restored':True,'error_content_excluded':True,
    'real_model_or_oauth_calls':0,'limits':'Inference module is synthetic here; actual profile source/dependency behavior requires additional controlled tests.'}))
