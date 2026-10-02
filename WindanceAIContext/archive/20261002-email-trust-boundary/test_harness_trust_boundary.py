"""Full isolated ASGI source-trust matrix; no real requests or service changes."""
import asyncio,importlib.util,json,os,sys,tempfile
from pathlib import Path
source=Path(sys.argv[1]).resolve();sys.path.insert(0,str(source.parent))
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp).resolve()
    for key in ('DATA','CONFIG','LOG'):os.environ['AGENT_HARNESS_'+key+'_DIR']=str(root)
    for key in ('GOOGLE_WORKSPACE_CONFIG_DIR','EXCALIDRAW_DIR'):os.environ[key]=str(root)
    os.environ['AGENT_HARNESS_TOKEN']=''
    def guard(event,args):
        if event in ('socket.connect','socket.bind','socket.sendto','subprocess.Popen','os.system','os.posix_spawn'):raise AssertionError('External effect forbidden')
        if event=='sqlite3.connect':assert str(root) in os.fsdecode(args[0])
        if event=='open' and not isinstance(args[0],int):
            path,mode,flags=args
            if (flags or 0)&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):assert Path(os.fsdecode(path)).resolve().is_relative_to(root)
    sys.addaudithook(guard)
    spec=importlib.util.spec_from_file_location('trust_fixture',source);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h);h.startup()
    assert '127.0.0.1' in h.TRUSTED_HARNESS_CLIENTS and '198.51.100.123' not in h.TRUSTED_HARNESS_CLIENTS
    import httpx
    outcomes=[]
    async def probe(ip,token,headers,path='/team',method='GET'):
        h.HARNESS_TOKEN=token
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=(ip,4321)),base_url='http://fixture') as c:
            r=await c.request(method,path,headers=headers,json={} if method=='POST' else None)
            return r.status_code
    async def run():
        for token in ('','synthetic-token'):
            for method,path in [('GET','/team'),('GET','/staff/tasks'),('GET','/permissions'),('POST','/message'),('POST','/gmail/action/approval'),('POST','/action/plan')]:
                code=await probe('198.51.100.123',token,{'X-Forwarded-For':'127.0.0.1'},path,method)
                assert code==401;outcomes.append(code)
        assert await probe('198.51.100.123','',{},'/health')==200
        assert await probe('127.0.0.1','',{})==200
        assert await probe('127.0.0.1','synthetic-token',{})==401
        assert await probe('198.51.100.123','synthetic-token',{'Authorization':'Bearer synthetic-token'})==200
        assert await probe('198.51.100.123','synthetic-token',{'Authorization':'Bearer wrong'})==401
        # This handler relies only on trusted-source middleware, even with token configured.
        assert await probe('127.0.0.1','synthetic-token',{},'/permissions')==200
    asyncio.run(run())
    with h.db() as c:
        assert c.execute('SELECT count(*) FROM approvals').fetchone()[0]==0
        assert c.execute('SELECT count(*) FROM staff_tasks').fetchone()[0]==0
print(json.dumps({'status':'passed','untrusted_prehandler_denials':len(outcomes),'forwarded_header_not_accepted_by_application':True,'trusted_loopback_allowed_without_configured_token':True,'configured_token_required_by_team_handler':True,'permissions_route_uses_source_trust_only':True,'real_network_calls':0,'production_changes':False,'limit':'ASGI scope simulation, not real proxy/firewall verification or per-user identity authorization'}))
