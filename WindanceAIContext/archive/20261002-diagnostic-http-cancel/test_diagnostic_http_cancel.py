"""Actual HTTP cancel acknowledgment for known running isolated worker."""
import hashlib,json,secrets,socket,subprocess,sys,tempfile,threading,time,urllib.request,urllib.error
from pathlib import Path
import uvicorn
from diagnostic_job_api import create_app
from diagnostic_remote_adapter import cancel_once
worker,launcher,evidence=sys.argv[1:]
with tempfile.TemporaryDirectory() as folder:
    token=secrets.token_urlsafe(32)
    app=create_app(Path(folder)/'jobs.db',{hashlib.sha256(token.encode()).hexdigest():'fixture'},
                   cancel_adapter=lambda ledger,key:cancel_once(ledger,key,worker))
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    proc=None;cid=None
    try:
        deadline=time.monotonic()+5
        while not server.started:assert time.monotonic()<deadline;time.sleep(.02)
        def call(method,path,body=None):
            req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,method=method,
                 data=json.dumps(body).encode() if body is not None else None,
                 headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
            try:
                with urllib.request.urlopen(req,timeout=20) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as e:return e.code,json.load(e)
        body={'request_key':'cancel-test','kind':'email_payload_diagnosis','evidence_sha256':evidence}
        key=call('POST','/jobs',body)[1]['id'];assert app.state.ledger.claim(key)
        # Operator-only slow fixture; API body cannot select arbitrary execution modes.
        args=['ssh','-o','BatchMode=yes','AL','python3','/tmp/windance-bounded-diagnosis-20261002/bounded_diagnosis_job_r4.py','timeout',key,evidence,worker,'--retain-container']
        proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        # Observe exact job's container before attempting cancellation.
        probe="import json,subprocess;from pathlib import Path;p=Path('/tmp/windance-bounded-diagnosis-20261002/job-"+key+"/container.json');i=json.loads(p.read_text());a=json.loads(subprocess.check_output(['docker','inspect',i['id']]))[0];print(json.dumps({'id':i['id'],'running':a['State']['Running']}))"
        deadline=time.monotonic()+2
        while True:
            p=subprocess.run(['ssh','-o','BatchMode=yes','AL','python3','-'],input=probe,capture_output=True,text=True,timeout=3)
            if p.returncode==0:
                observed=json.loads(p.stdout);cid=observed['id']
                if observed['running']:break
            assert time.monotonic()<deadline;time.sleep(.03)
        code,cancel=call('POST','/jobs/'+key+'/cancel')
        assert code==200 and cancel['state']=='cancelled' and cancel['worker_stopped'] is True
        assert call('GET','/jobs/'+key+'/result')[0]==409
        assert call('POST','/jobs',body)[1]['state']=='cancelled'
        assert not app.state.ledger.claim(key)
        out,err=proc.communicate(timeout=8);assert proc.returncode==0
        summary={'actual_http_cancel_acknowledged':True,'exact_worker_stopped':True,'result_unavailable':True,'retry_claim_denied':True,'job_id':key}
    finally:
        if proc and proc.poll() is None:proc.communicate(timeout=8)
        if cid:
            assert len(cid)==64 and all(c in '0123456789abcdef' for c in cid)
            subprocess.run(['ssh','AL','docker','rm','-f','-v',cid],check=True,stdout=subprocess.DEVNULL,timeout=10)
        server.should_exit=True;thread.join(timeout=5);sock.close();assert not thread.is_alive()
    summary['test_cleanup_verified']=True
    Path('/tmp/diagnostic-http-cancel-results.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
