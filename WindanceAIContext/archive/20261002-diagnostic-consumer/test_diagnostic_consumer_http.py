"""Real loopback HTTP -> scoped ledger -> SSH AL worker -> protected result."""
import hashlib,json,secrets,socket,sys,tempfile,threading,time,urllib.request,urllib.error
from pathlib import Path
import uvicorn
from diagnostic_job_api import create_app
from diagnostic_consumer import run_cycle
worker,launcher,evidence=sys.argv[1:]
with tempfile.TemporaryDirectory() as folder:
    tokens=[secrets.token_urlsafe(32) for _ in range(2)]
    config={hashlib.sha256(t.encode()).hexdigest():p for t,p in zip(tokens,['principal-a','principal-b'])}
    app=create_app(Path(folder)/'jobs.db',config)
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    try:
        deadline=time.monotonic()+5
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.02)
        def call(method,path,token=None,body=None):
            req=urllib.request.Request('http://127.0.0.1:'+str(port)+path,method=method,
                data=json.dumps(body).encode() if body is not None else None,
                headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})
            try:
                with urllib.request.urlopen(req,timeout=5) as response:return response.status,json.load(response)
            except urllib.error.HTTPError as exc:return exc.code,json.load(exc)
        body={'request_key':'actual-http','kind':'email_payload_diagnosis','evidence_sha256':evidence}
        assert call('POST','/jobs',body=body)[0]==401
        code,created=call('POST','/jobs',tokens[0],body);assert code==200
        key=created['id'];assert call('GET','/jobs/'+key+'/result',tokens[0])[0]==409
        executed=run_cycle(app.state.ledger,worker,launcher);assert executed=={'started':True,'state':'completed','job_id':key}
        code,result=call('GET','/jobs/'+key+'/result',tokens[0]);assert code==200
        assert result['job_id']==key and result['result']['status']=='diagnosed'
        assert call('GET','/jobs/'+key+'/result',tokens[1])[0]==404
        again=call('POST','/jobs',tokens[0],body)[1];assert again['id']==key and again['reused']
        assert run_cycle(app.state.ledger,worker,launcher)=={'started':False,'state':'idle'}
        summary={'http_authenticated':True,'unauthenticated_denied':True,'cross_owner_result_denied':True,
                 'actual_worker_completed':True,'duplicate_started':False,'job_id':key,
                 'terminal_sha256':result['terminal_sha256'],'persistent_service':False}
    finally:
        server.should_exit=True;thread.join(timeout=5);sock.close();assert not thread.is_alive()
    summary['listener_stopped_verified']=True
    Path('/tmp/diagnostic-consumer-http-results.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))

