"""Actual staged caller -> loopback Uvicorn/Harness -> fixed empty sweep worker."""
import ast,contextlib,hashlib,importlib.util,io,json,os,secrets,socket,sys,tempfile,threading,time,urllib.request
from pathlib import Path
stage=Path(sys.argv[1]).resolve();caller=Path(sys.argv[2]).resolve();sys.path.insert(0,str(stage))
assert hashlib.sha256(caller.read_bytes()).hexdigest()=='d282c158355b9d937e7175193eadd56d331fc8d07d45542c4bbe2ef7cd672aef'
assert hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()=='d9dd9a97324d7ee1bbc5d1758a5670a78c54d35332cdaa8626fbc46bbf12e1ec'
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for name in ('DATA','CONFIG','LOG'):os.environ['AGENT_HARNESS_'+name+'_DIR']=str(root)
    os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(root)
    token=secrets.token_urlsafe(32);os.environ['AGENT_HARNESS_TOKEN']=token
    spec=importlib.util.spec_from_file_location('sweep_http_integration',stage/'agent_harness.py')
    h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
    assert h.DB_FILE.resolve().is_relative_to(root.resolve());h.startup()
    import email_process_deadline as deadline,uvicorn
    original=deadline.run;launches=[]
    def tracked(*a,**k):launches.append(a[1]['operation']);return original(*a,**k)
    deadline.run=tracked
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(h.app,host='127.0.0.1',port=port,log_level='critical',access_log=False,lifespan='off'))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    try:
        until=time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic()<until:time.sleep(.02)
        assert server.started
        tree=ast.parse(caller.read_text());nodes=[n for n in tree.body if getattr(n,'name','') in ('main','post_json')]
        env={'json':json,'urllib':__import__('urllib'),'HARNESS_SWEEP_URL':f'http://127.0.0.1:{port}/gmail/sender-rules/sweep',
             'NODE_RED_SEND_URL':'invalid-notice-endpoint-never-call','PHONE':'synthetic'}
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<actual-caller>','exec'),env)
        def invoke():
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):status=env['main']()
            return status,json.loads(buf.getvalue())
        cases=[]
        os.environ.pop('AGENT_HARNESS_TOKEN')
        status,result=invoke();assert status==1 and not launches
        cases.append('missing_client_auth_no_worker')
        os.environ['AGENT_HARNESS_TOKEN']='synthetic-wrong'
        status,result=invoke();assert status==1 and not launches
        cases.append('wrong_client_auth_no_worker')
        os.environ['AGENT_HARNESS_TOKEN']=token
        status,result=invoke();assert status==0 and result=={'status':'sweep_completed','checked':0,'deleted':0,'notification_attempted':False}
        assert launches==['sender_rule_sweep'];cases.append('authenticated_empty_real_worker_success')
        h.HARNESS_TOKEN=''
        status,result=invoke();assert status==1 and len(launches)==1
        cases.append('unconfigured_server_no_worker')
        assert not h.GOOGLE_TOKEN_FILE.exists()
        print(json.dumps({'cases':cases,'actual_worker_launches':len(launches),'real_provider_or_notice_calls':0,
            'production_changes':False,'limits':'Actual empty sweep only, synthetic token and isolated data. Natural schedule/nonempty real mailbox/delivery still unverified.'}))
    finally:
        server.should_exit=True;thread.join(10);sock.close();assert not thread.is_alive()
        deadline.run=original
