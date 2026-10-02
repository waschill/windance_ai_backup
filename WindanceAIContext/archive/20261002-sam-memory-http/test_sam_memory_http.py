"""Real temporary HTTP producer boundary, actual secret classifier and durable client."""
import ast,json,re,secrets,socket,sqlite3,tempfile,threading,time,urllib.request,urllib.error
from pathlib import Path
import uvicorn
import sam_memory_client as client
from sam_business_memory import SCHEMA
from sam_business_memory_api import create_app
source=Path('/Users/herald/services/agent-harness/agent_harness.py').read_text()
node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='memory_looks_secret')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-secret-classifier>','exec'),ns)
class Closing(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);token=secrets.token_urlsafe(32)
    def remote():return sqlite3.connect(root/'receiver.db',factory=Closing)
    def local():return sqlite3.connect(root/'client.db',factory=Closing)
    with remote() as c:c.executescript(SCHEMA)
    with local() as c:c.executescript(client.SCHEMA)
    app=create_app(remote,token,lambda text:not ns['memory_looks_secret'](text))
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False))
    thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
    calls=[]
    try:
        deadline=time.monotonic()+5
        while not server.started:assert time.monotonic()<deadline;time.sleep(.02)
        def http(envelope,auth=token,method='POST'):
            req=urllib.request.Request(f'http://127.0.0.1:{port}/memory/business/sam-schedule',method=method,
              data=json.dumps(envelope).encode() if method=='POST' else None,
              headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+auth} if auth else {})})
            try:
                with urllib.request.urlopen(req,timeout=3) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as e:return e.code,json.load(e)
        payload={'kind':'sam_daily_schedule','key':'2026-10-01','value':'Synthetic daily summary','confidence':.92,'source':'SAM schedule display'}
        envelope={'event_id':'test','expected_revision':0,'payload':payload}
        assert http(envelope,None)[0]==403 and http(envelope,'invalid')[0]==403
        assert http(envelope,method='GET')[0]==405
        assert http({**envelope,'owner':'william'})[0]==422
        assert http({**envelope,'expected_revision':True})[0]==422
        assert http({**envelope,'payload':{**payload,'kind':'preference'}})[0]==403
        secret=http({**envelope,'payload':{**payload,'value':'Synthetic password: PRIVATE_SENTINEL'}})
        assert secret[0]==403 and 'PRIVATE_SENTINEL' not in json.dumps(secret)
        def transport(body):
            calls.append(body['event_id']);code,receipt=http(body);assert code==200
            if len(calls)==1:raise OSError('Synthetic lost acknowledgment')
            return receipt
        try:client.submit(local,payload,transport)
        except OSError:pass
        else:raise AssertionError('Loss injection failed')
        receipt=client.submit(local,payload,transport)
        assert len(calls)==2 and len(set(calls))==1 and receipt['revision']==1
        assert client.submit(local,payload,transport)==receipt and len(calls)==2
        with remote() as c:assert c.execute('SELECT count(*) FROM sam_business_receipts').fetchone()[0]==1
        assert http({'event_id':calls[0],'expected_revision':0,'payload':{**payload,'value':'changed'}})[0]==409
        summary={'actual_http':True,'missing_wrong_credentials_denied':True,'no_read_route':True,
                 'owner_private_kind_and_boolean_revision_denied':True,'actual_secret_classifier_fixture_denied':True,
                 'lost_response_same_event_recovered':True,'receiver_commits':1,'cached_retry_http_calls':0}
    finally:
        server.should_exit=True;thread.join(timeout=5);sock.close();assert not thread.is_alive()
    summary['listener_stopped_verified']=True
    Path('/tmp/sam-memory-http-results.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
