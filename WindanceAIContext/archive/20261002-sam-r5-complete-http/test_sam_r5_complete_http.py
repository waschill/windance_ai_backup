"""Full staged SAM import and real producer HTTP in a network-none container."""
import hashlib,importlib.util,json,os,secrets,socket,sqlite3,sys,tempfile,threading,time
from pathlib import Path
from unittest.mock import patch
import uvicorn
assert os.geteuid()!=0 and [name for _,name in socket.if_nameindex()]==['lo']
os.umask(0o077)
source_root=Path('/evidence/sam-memory-r5-private')
manifest=json.loads((source_root/'memory-r5-manifest.json').read_text())
assert all(hashlib.sha256((source_root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
assert manifest['sam_schedule.memory-r5.private.py']=='1e6a553a34ed27b6d1f51cba00d3c473843fee4f351e581cf4ac7282a8ffbdcf'
sys.path.insert(0,str(source_root))
from sam_business_memory import SCHEMA
from sam_business_memory_api import create_app
import sam_memory_transport
class Closing(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
results=[]
for mode in ('normal','lost_response','wrong_credential_then_corrected'):
    with tempfile.TemporaryDirectory(prefix='sam-complete-http-') as directory:
        root=Path(directory);token=secrets.token_urlsafe(32);credential=root/'producer.secret'
        credential.write_text(token)
        def remote():return sqlite3.connect(root/'receiver.db',factory=Closing)
        with remote() as c:c.executescript(SCHEMA)
        # Synthetic content only. Secret-classifier behavior is independently
        # covered; this fixture does not assert its production integration.
        app=create_app(remote,token,lambda _:True)
        sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False))
        thread=threading.Thread(target=lambda:server.run(sockets=[sock]),daemon=True);thread.start()
        calls=[];errors=[]
        try:
            deadline=time.monotonic()+5
            while not server.started:assert time.monotonic()<deadline;time.sleep(.02)
            env={'SAM_SCHEDULE_HOME':str(root),'SAM_SCHEDULE_DATA':str(root),'SAM_SCHEDULE_DB':str(root/'sam.db'),
                 'SAM_SCHEDULE_ASSETS':str(root/'assets'),'SAM_SCHEDULE_HOST':'127.0.0.1','SAM_SCHEDULE_PORT':'0',
                 'SAM_BUSINESS_MEMORY_URL':f'http://127.0.0.1:{port}/memory/business/sam-schedule',
                 'SAM_BUSINESS_MEMORY_CREDENTIAL_FILE':str(credential)}
            with patch.dict(os.environ,env):
                spec=importlib.util.spec_from_file_location('isolated_sam_'+mode,source_root/'sam_schedule.memory-r5.private.py')
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                assert module.DB_PATH==root/'sam.db'
                module.init_db()
                with module.connect() as c:
                    c.execute("INSERT INTO schedule_days(date,day_name) VALUES('2099-01-01','fixture')")
                    c.execute("INSERT INTO schedule_items(id,date,horse_key,horse_name,odoo_schedule_row_id,training_raw,updated_at) VALUES('fixture','2099-01-01','fixture','SYNTHETIC',1,'A','fixture')")
                    c.commit()
                original_send=sam_memory_transport.send
                def send(url,path,envelope):
                    calls.append(envelope['event_id'])
                    result=original_send(url,path,envelope)
                    if mode=='lost_response' and len(calls)==1:raise RuntimeError('Synthetic acknowledgment loss after real HTTP')
                    return result
                if mode=='wrong_credential_then_corrected':credential.write_text(secrets.token_urlsafe(32))
                with patch.object(sam_memory_transport,'send',send):
                    for attempt in range(3):
                        try:module.commit_day('2099-01-01');errors.append(False)
                        except RuntimeError:errors.append(True)
                        if attempt==0:credential.write_text(token)
                assert errors==([False]*3 if mode=='normal' else [True,False,False])
                assert len(calls)==(1 if mode=='normal' else 2) and len(set(calls))==1
                with module.connect() as c:
                    assert c.execute('SELECT committed FROM schedule_days').fetchone()[0]==1
                    assert c.execute('SELECT count(*) FROM missed_training').fetchone()[0]==1
                    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                with remote() as c:assert c.execute('SELECT count(*) FROM sam_business_receipts').fetchone()[0]==1
        finally:
            server.should_exit=True;thread.join(5);sock.close();assert not thread.is_alive()
        results.append({'scenario':mode,'http_transport_attempts':len(calls),'receiver_commits':1,'stable_event':True,'local_committed':True,'listener_stopped':True})
print(json.dumps({'full_candidate_import':True,'actual_producer_api_and_transport':True,'cases':results,'production_changes':False,'external_calls':0,'scheduler_or_main_started':False,'limits':'Synthetic data and content validator; no production credentials/TLS, Odoo or correction workflow'}))
