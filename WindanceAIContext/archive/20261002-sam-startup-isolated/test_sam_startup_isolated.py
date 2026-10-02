"""Run only via sudo unshare --net; full candidate startup with inactive producers."""
import contextlib, hashlib, importlib.util, io, json, os, pathlib, pwd, shutil, socket, sqlite3, subprocess, tempfile, threading, urllib.request
from contextlib import closing
assert os.geteuid()==0
assert os.readlink('/proc/self/ns/net')!=os.readlink('/proc/1/ns/net'), 'Separate network namespace required'
assert [name for _,name in socket.if_nameindex()]==['lo']
subprocess.run(['/usr/sbin/ip','link','set','lo','up'],check=True)
account=pwd.getpwnam('williamschilling')
os.initgroups(account.pw_name,account.pw_gid);os.setgid(account.pw_gid);os.setuid(account.pw_uid)
assert os.geteuid()==account.pw_uid and os.geteuid()!=0
os.umask(0o077)
source=pathlib.Path('/home/williamschilling/backups/sam-reliability-candidate-20261002/sam_schedule.candidate.private.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='148adcb085f0e51264b3b1d5d811f5d34c2ce8fba5a934b8a27b9c97156ee8a5'
assert hashlib.sha256(pathlib.Path('/tmp/sam_history_intent.py').read_bytes()).hexdigest()=='bdb0193cebecefc918c0b11ef763ce64d363bf64a3f744a8b2b3e304e9847b01'
snapshot=pathlib.Path('/home/williamschilling/backups/sam-existing-db-recovery-20261002T024254Z/snapshot.private.db')
def tables(path):
    with closing(sqlite3.connect(path)) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()==('ok',)
        return {t:sorted(repr(tuple(r)) for r in c.execute('SELECT * FROM "'+t.replace('"','""')+'"')) for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
before=tables(snapshot);calls=[];statuses={};server_threads=[]
with tempfile.TemporaryDirectory(prefix='sam-isolated-startup-') as folder:
    root=pathlib.Path(folder);db=root/'restored.private.db';shutil.copyfile(snapshot,db)
    os.environ.update(SAM_SCHEDULE_HOME=str(root),SAM_SCHEDULE_DATA=str(root),SAM_SCHEDULE_DB=str(db),SAM_SCHEDULE_ASSETS=str(root/'assets'),SAM_SCHEDULE_HOST='127.0.0.1',SAM_SCHEDULE_PORT='0')
    spec=importlib.util.spec_from_file_location('sam_isolated_candidate',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.DB_PATH==db and module.HOST=='127.0.0.1' and module.PORT==0
    # Prevent startup producers and scheduling. Real init, routing, DB readers,
    # HTML rendering and HTTP handling remain unchanged.
    for name in ['fetch_schedule','fetch_weather_alerts','fetch_weather_widget','scheduler_loop']:
        setattr(module,name,lambda *a,_name=name,**k:calls.append(_name))
    real_server=module.ThreadingHTTPServer
    class CheckedServer(real_server):
        def serve_forever(self):
            server_threads.append(threading.Thread(target=lambda:real_server.serve_forever(self,poll_interval=0.05),daemon=True))
            server_threads[-1].start()
            try:
                base='http://127.0.0.1:'+str(self.server_port)
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                for route in ['/health','/','/admin','/api/schedule','/api/trainers']:
                    with opener.open(base+route,timeout=5) as reply:
                        body=reply.read();assert reply.status==200;statuses[route]=reply.status
                        if route=='/health':assert json.loads(body)['status']=='ok'
                        elif route=='/api/schedule':assert isinstance(json.loads(body)['items'],list)
                        elif route=='/api/trainers':assert isinstance(json.loads(body)['trainers'],list)
                        else:assert b'<html' in body.lower()
            finally:
                self.shutdown();self.server_close();server_threads[-1].join(5)
                assert not server_threads[-1].is_alive()
    module.ThreadingHTTPServer=CheckedServer
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):module.main()
    after=tables(db)
    assert set(after)==set(before)|{'sam_history_intents'} and not after['sam_history_intents']
    assert all(after[k]==v for k,v in before.items())
    assert calls.count('scheduler_loop')==1 and calls.count('fetch_weather_alerts')==1 and calls.count('fetch_weather_widget')==1
print(json.dumps({'separate_loopback_only_network_namespace':True,'ran_as_unprivileged_sam_user':True,'full_candidate_import_and_main':True,'get_routes':statuses,'producer_and_scheduler_calls_intercepted':calls,'existing_tables_preserved':len(before),'server_stopped':True,'production_changes':False,'actual_remote_calls':0,'limits':'Producer/scheduler bodies intentionally inactive; no browser render, real commit, reconciliation or live deployment acceptance'}))
