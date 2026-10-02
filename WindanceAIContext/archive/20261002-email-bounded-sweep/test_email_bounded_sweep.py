"""Actual ASGI/packaged empty sweep plus boundary and uncertainty contracts."""
import asyncio,importlib.util,json,os,secrets,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
with tempfile.TemporaryDirectory() as tmp:
    scratch=Path(tmp)
    for name in ('DATA','CONFIG','LOG'):os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
    os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch)
    token=secrets.token_urlsafe(32);os.environ['AGENT_HARNESS_TOKEN']=token
    spec=importlib.util.spec_from_file_location('sweep_candidate',stage/'agent_harness.py')
    h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
    assert h.DB_FILE.resolve().is_relative_to(scratch.resolve());h.startup()
    import email_process_deadline as deadline,email_owner_boundary as owner,httpx
    original=deadline.run;calls=[]
    def tracked(*args,**kwargs):
        assert args[1]['operation']=='sender_rule_sweep' and kwargs['timeout']==120
        calls.append('worker');return original(*args,**kwargs)
    deadline.run=tracked
    empty={'rules':0,'checked':0,'deleted':0,'kept':0,'notices':[],'errors':[]}
    codes=[]
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://fixture') as c:
            path='/gmail/sender-rules/sweep'
            for headers in ({},{'Authorization':'Bearer wrong'}):
                r=await c.post(path,headers=headers);assert r.status_code==401;codes.append(r.status_code)
            saved=h.HARNESS_TOKEN;h.HARNESS_TOKEN=''
            r=await c.post(path);assert r.status_code==503 and not calls;codes.append(r.status_code)
            h.HARNESS_TOKEN=saved;headers={'Authorization':'Bearer '+token}
            r=await c.post(path,headers=headers);assert r.status_code==200 and r.json()==empty and len(calls)==1;codes.append(r.status_code)
            def failure(*a,**k):raise TimeoutError('PRIVATE_SENTINEL')
            deadline.run=failure
            r=await c.post(path,headers=headers);assert r.status_code==502 and 'PRIVATE_SENTINEL' not in r.text and 'outcome unavailable' in r.text;codes.append(r.status_code)
            for receipt in ({},dict(empty,deleted=True),dict(empty,deleted=1),dict(empty,status='complete'),dict(empty,errors=['PRIVATE_SENTINEL'],extra=True)):
                deadline.run=lambda *a,**k:receipt
                r=await c.post(path,headers=headers);assert r.status_code==502 and 'PRIVATE_SENTINEL' not in r.text
            deadline.run=lambda *a,**k:dict(empty,status='held',errors=['listing unavailable'])
            r=await c.post(path,headers=headers);assert r.status_code==503;codes.append(r.status_code)
    asyncio.run(check())
    deadline.run=tracked
    @owner.bind_mailbox_owner
    def other(payload):return h.gmail_sender_rule_sweep()
    result=other(SimpleNamespace(user='shawn'));assert result['model']=='mailbox-owner-denied' and len(calls)==1
    deadline.run=original
    print(json.dumps({'http_codes':codes,'actual_empty_worker_launches':len(calls),'malformed_receipts_rejected':5,'owner_rejected_before_spawn':True,'timeout_is_uncertain_not_success':True,'real_provider_or_model_calls':0,'limits':'Empty real worker; timeout and malformed receipts injected. Nonempty sweep integration remains unverified.'}))
