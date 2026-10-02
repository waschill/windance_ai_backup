"""Actual sweep and endpoint code; synthetic provider, before/after comparison."""
import ast,hashlib,json,re
from pathlib import Path
from typing import Any
prior=Path(r'C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-route-package\candidate.private.py')
current=Path(__file__).parent/'email-sweep-hold-r2-private'
manifest=json.loads((current/'manifest.json').read_text())
assert all(hashlib.sha256((current/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
class HTTPError(Exception):
    def __init__(self,status_code,detail):self.status_code=status_code;self.detail=detail
results=[]
for version,path in (('before',prior),('after',current/'agent_harness.candidate.private.py')):
    source=path.read_text(encoding='utf-8')
    nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in {'gmail_sender_rule_sweep','post_gmail_sender_rule_sweep','direct_email_domain_rule'}]
    assert len(nodes)==3
    for n in nodes:n.decorator_list=[]
    for mode in ('normal','list_first','list_second','metadata','service','apply'):
        calls=[];actions=[];audits=[]
        class Request:
            def __init__(self,kind,args):self.kind=kind;self.args=args
            def execute(self,**kwargs):
                if version=='after':assert kwargs=={'num_retries':0}
                calls.append(self.kind)
                if self.kind=='list':
                    if mode=='list_first' or mode=='list_second' and len(calls)>2:raise RuntimeError('PRIVATE_SENTINEL')
                    return {'messages':[{'id':'one' if len(calls)==1 else 'two'}]}
                if mode=='metadata':raise RuntimeError('PRIVATE_SENTINEL')
                return {'id':self.args['id']}
        class Gmail:
            def users(self):return self
            def messages(self):return self
            def list(self,**kwargs):return Request('list',kwargs)
            def get(self,**kwargs):return Request('get',kwargs)
        def service():
            if mode=='service':raise RuntimeError('PRIVATE_SENTINEL')
            return Gmail()
        def apply(items):
            actions.append(len(items))
            if mode=='apply':raise RuntimeError('PRIVATE_SENTINEL')
            return [],[]
        ns={'Any':Any,'re':re,'upsert_email_domain_rule':lambda action,domain:'@'+domain,'email_sender_rules':lambda:{'a@example.invalid':{'action':'always_delete'},'b@example.invalid':{'action':'always_delete'}},
            'gmail_service':service,'message_summary':lambda x,**k:x,'apply_email_sender_rules':apply,'audit':lambda *a:audits.append(a),
            'Header':lambda **k:None,'require_token':lambda token:None,'HTTPException':HTTPError}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-sweep>','exec'),ns)
        try:result=ns['post_gmail_sender_rule_sweep'](authorization='fixture')
        except HTTPError as exc:result={'status_code':exc.status_code,'detail':exc.detail}
        leaked='PRIVATE_SENTINEL' in json.dumps([result,audits])
        if version=='after':
            assert not leaked
            if mode in ('list_first','list_second','metadata'):
                assert not actions and result['status_code']==503
            elif mode in ('service','apply'):assert result['status_code']==502
            else:assert result['deleted']==2 and actions==[2]
        elif mode!='normal':assert leaked
        if version=='before' and mode=='list_second':assert actions==[1]
        if version=='after':
            actions.clear();calls.clear();audits.clear()
            reply=ns['direct_email_domain_rule']('always delete example.invalid')
            assert 'PRIVATE_SENTINEL' not in json.dumps([reply,audits])
            if mode!='normal':assert reply[2]=='gmail-domain-rule-held' and 'Done.' not in reply[0]
            if mode in ('list_first','list_second','metadata','service'):assert not actions
        results.append({'version':version,'scenario':mode,'raw_error_leaked':leaked,'action_batch_calls':len(actions),'simulated_items_submitted':sum(actions)})
print(json.dumps({'cases':results,'candidate_sha256':manifest['agent_harness.candidate.private.py'],'production_changes':False,'real_mailbox_calls':0,'limits':'Endpoint function, not live ASGI/provider; apply-stage unknown effects still require durable recovery.'}))
