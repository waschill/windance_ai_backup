"""Pinned original loop -> pause lease -> actual new worker, synthetic transport."""
import hashlib,importlib.util,json,os,select,signal,subprocess,sys,tempfile,time
from pathlib import Path
from receiver_pause_guard import inspect

def wait_for(predicate,seconds=4):
    deadline=time.monotonic()+seconds
    while not predicate():
        if time.monotonic()>deadline:raise AssertionError('fixture condition timeout')
        time.sleep(.02)

def child(mode,source,root):
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'
    spec=importlib.util.spec_from_file_location('original_receiver_fixture',source)
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    host.ROOT=root;host.QUEUE=root/'queue';host.RESULTS=root/'results';host.LOG=root/'test.log'
    def log(message):
        if message=='outbox_started':(root/'ready').write_text('ready')
    host.log=log
    def send(*args):
        with (root/'effects').open('a') as f:f.write(mode+'\n')
        if (root/'hold_send').exists():wait_for(lambda:(root/'release_send').exists(),8)
    host.send_one=send
    if mode=='old':host.main()
    else:
        from receipt_request_worker import process_one
        assert process_one(host,'request',root/'unused.db',root/'unused.whl',contract='auto')=='processed_legacy'
    return

if len(sys.argv)>2:
    child(sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3]));raise SystemExit(0)
source=Path(sys.argv[1]).resolve();results=[]
with tempfile.TemporaryDirectory(prefix='receiver-handoff-') as tmp:
    for case in ('inflight_abort','arrival_during_idle_switch'):
        root=Path(tmp)/case;root.mkdir()
        for folder in ('queue','results','claims','inflight','uncertain'):(root/folder).mkdir()
        payload={'to':'synthetic-owner','chunks':['synthetic body'],'sms':False}
        if case=='inflight_abort':
            (root/'hold_send').touch();(root/'queue/request.json').write_text(json.dumps(payload))
        old=subprocess.Popen([sys.executable,'-B',__file__,'old',str(source),str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        guard=None
        try:
            wait_for(lambda:(root/'ready').exists())
            if case=='inflight_abort':wait_for(lambda:(root/'effects').exists())
            identity=inspect(old.pid)[0]
            guard=subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('receiver_pause_guard.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
            guard.stdin.write((json.dumps({'pid':old.pid,'identity':identity,'seconds':5})+'\n').encode());guard.stdin.flush()
            assert select.select([guard.stdout],[],[],3)[0]
            assert json.loads(guard.stdout.readline())['status']=='paused'
            busy=any(any((root/folder).iterdir()) for folder in ('queue','inflight','uncertain'))
            if case=='inflight_abort':
                assert busy and (root/'inflight/request.json').exists()
                guard.stdin.write(b'resume\n');guard.stdin.flush();guard.wait(timeout=3)
                assert guard.returncode==0 and old.poll() is None
                (root/'release_send').touch()
                wait_for(lambda: not (root/'queue/request.json').exists() and not (root/'inflight/request.json').exists())
                assert (root/'effects').read_text()=='old\n'
            else:
                assert not busy
                # Arrival AFTER the idle check: old process is still stopped.
                (root/'queue/request.json').write_text(json.dumps(payload))
                assert 'T' in inspect(old.pid)[1] and guard.poll() is None
                old.kill();old.wait(timeout=3)
                guard.stdin.close();guard.wait(timeout=3);assert guard.returncode==0
                assert not (root/'effects').exists() and (root/'queue/request.json').exists()
                new=subprocess.run([sys.executable,'-B',__file__,'new',str(source),str(root)],capture_output=True,timeout=4)
                assert new.returncode==0
                assert (root/'effects').read_text()=='new\n' and not (root/'queue/request.json').exists()
            assert json.loads((root/'results/request.json').read_text())=={'ok':True,'chunks':1}
            results.append(case)
        finally:
            if guard is not None:
                if guard.stdin and not guard.stdin.closed:guard.stdin.close()
                guard.wait(timeout=4);guard.stdout.close()
            if old.poll() is None:
                os.kill(old.pid,signal.SIGCONT);old.terminate();old.wait(timeout=3)
print(json.dumps({'status':'passed','cases':results,'inflight_abort_resumed':True,'new_arrival_preserved':True,'duplicate_synthetic_effects':0,'production_processes_signaled':0,'launchctl_tested':False,'real_sends':0}))
