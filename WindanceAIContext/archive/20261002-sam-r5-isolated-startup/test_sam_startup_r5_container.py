"""Run only in verified network-none readonly container; no active producers."""
import contextlib, hashlib, importlib.util, io, json, os, pathlib, pwd, shutil, socket, sqlite3, subprocess, tempfile, threading, urllib.request
from contextlib import closing
assert os.geteuid()!=0
assert [name for _,name in socket.if_nameindex()]==['lo']
os.umask(0o077)
root_source=pathlib.Path('/evidence/sam-memory-r5-private')
manifest=json.loads((root_source/'memory-r5-manifest.json').read_text())
assert all(hashlib.sha256((root_source/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=root_source/'sam_schedule.memory-r5.private.py'
assert manifest[source.name]=='1e6a553a34ed27b6d1f51cba00d3c473843fee4f351e581cf4ac7282a8ffbdcf'
import sys
sys.path.insert(0,str(root_source))
snapshot=pathlib.Path('/evidence/snapshot.private.db')
assert hashlib.sha256(snapshot.read_bytes()).hexdigest()=='19223b6adb07b25ba91dca206a65507a310e808a7bf0a66c52ae44020b105f66'

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
    added={'sam_history_intents','sam_clear_intents','sam_memory_requests','sam_commit_snapshots','sam_rollover_receipts'}
    assert set(after)==set(before)|added and all(not after[t] for t in added)
    assert all(after[k]==v for k,v in before.items())
    cold=root/'cold-restored.private.db';shutil.copyfile(db,cold)
    assert tables(cold)==after
    module.DB_PATH=cold;module.init_db();assert tables(cold)==after
    assert calls.count('scheduler_loop')==1 and calls.count('fetch_weather_alerts')==1 and calls.count('fetch_weather_widget')==1
print(json.dumps({'loopback_only_container':True,'ran_as_unprivileged_user':True,'candidate_files':len(manifest),'cold_restore_verified':True,'new_empty_tables':len(added),'full_candidate_import_and_main':True,'get_routes':statuses,'producer_and_scheduler_calls_intercepted':calls,'existing_tables_preserved':len(before),'server_stopped':True,'production_changes':False,'actual_remote_calls':0,'limits':'Producer/scheduler bodies intentionally inactive; no browser render, real commit, reconciliation or live deployment acceptance'}))
