"""Actual ASGI auth and real packaged worker with deliberately absent fixture credentials."""
import asyncio,importlib.util,json,os,secrets,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
with tempfile.TemporaryDirectory() as tmp:
    scratch=Path(tmp)
    for name in ['DATA','CONFIG','LOG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
    os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch)
    token=secrets.token_urlsafe(32);os.environ['AGENT_HARNESS_TOKEN']=token
    source=stage/'agent_harness.py'
    if not source.exists():source=stage/'agent_harness.candidate.private.py'
    spec=importlib.util.spec_from_file_location('email_http_candidate',source)
    h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
    assert h.GOOGLE_TOKEN_FILE.resolve().is_relative_to(scratch.resolve()) and not h.GOOGLE_TOKEN_FILE.exists()
    h.startup()
    import email_process_deadline as deadline,email_owner_boundary as owner,httpx
    original=deadline.run;launches=[]
    def tracked(*args,**kwargs):launches.append('worker');return original(*args,**kwargs)
    deadline.run=tracked
    codes=[]
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://fixture') as client:
            for headers in ({},{'Authorization':'Bearer wrong-fixture'}):
                r=await client.post('/gmail/report',json={},headers=headers);assert r.status_code==401;codes.append(r.status_code)
            assert not launches
            saved=h.HARNESS_TOKEN;h.HARNESS_TOKEN=''
            try:
                r=await client.post('/gmail/report',json={});assert r.status_code==503 and not launches;codes.append(r.status_code)
            finally:h.HARNESS_TOKEN=saved
            r=await client.post('/gmail/report',json={},headers={'Authorization':'Bearer '+token})
            assert r.status_code==503 and r.json()['model']=='gmail-error'
            assert len(launches)==1 and str(scratch) not in r.text and token not in r.text
            codes.append(r.status_code)
    asyncio.run(check())
    async def successful_receipt():
        deadline.run=lambda *a,**k:{'reply':'synthetic completed report','provider':'deterministic','model':'gmail-autonomy'}
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://fixture') as client:
                r=await client.post('/gmail/report',json={},headers={'Authorization':'Bearer '+token})
                assert r.status_code==200 and r.json()['reply']=='synthetic completed report';codes.append(r.status_code)
        finally:deadline.run=tracked
    asyncio.run(successful_receipt())
    # Existing message-owner boundary refuses before spawning a process.
    @owner.bind_mailbox_owner
    def other(payload):return h.summarize_email_for_william()
    rejected=other(SimpleNamespace(user='shawn'));assert rejected['model']=='mailbox-owner-denied' and len(launches)==1
    def unavailable(*a,**k):raise RuntimeError('PRIVATE_SENTINEL')
    deadline.run=unavailable
    result=h.summarize_email_for_william();assert result[2]=='gmail-error' and 'PRIVATE_SENTINEL' not in str(result)
    deadline.run=original
    print(json.dumps({'http_codes':codes,'unauthorized_or_unconfigured_launches':0,'authorized_real_subprocess_launches':1,
        'missing_fixture_account_report_invalid':True,'owner_rejected_before_spawn':True,'supervisor_error_sanitized':True,
        'limits':'Synthetic service token and absent fixture credentials; no real human/mailbox identity, nonempty live provider or deployment.'}))
