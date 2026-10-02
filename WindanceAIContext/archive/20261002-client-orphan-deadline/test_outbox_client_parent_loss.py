import hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
from message_receipt_journal import Journal

payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':False};key='synthetic'
if sys.argv[1:2]==['--parent']:
    root=Path(sys.argv[2]);mode=sys.argv[3]
    import bounded_outbox_status,bounded_outbox_client
    original=subprocess.Popen
    def spawn(*args,**kwargs):
        child=original(*args,**kwargs);(root/'worker.pid').write_text(str(child.pid));return child
    subprocess.Popen=spawn
    action=bounded_outbox_status.query if mode=='query' else bounded_outbox_client.submit_and_wait
    action(root,key,payload,seconds=.8)
    raise SystemExit(0)

results=[]
with tempfile.TemporaryDirectory(prefix='windance-client-parent-loss-') as tmp:
    for mode in ('query','submit'):
        root=Path(tmp)/mode;root.mkdir()
        for folder in ('claims','results','queue'):(root/folder).mkdir()
        Journal(root/'journal.db',create=True)
        name='key-'+hashlib.sha256(key.encode()).hexdigest()+'.json'
        if mode=='query':
            fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            (root/'claims'/name).write_text(json.dumps({'content_sha256':fingerprint}))
            (root/'queue'/name).write_text(json.dumps(payload))
        parent=subprocess.Popen([sys.executable,'-B',__file__,'--parent',str(root),mode],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+2
            while not (root/'worker.pid').exists() or not (root/'queue'/name).exists():
                assert parent.poll() is None and time.monotonic()<deadline
                time.sleep(.01)
            time.sleep(.1)
            pid=int((root/'worker.pid').read_text())
            parent.kill();parent.wait(timeout=2)
            deadline=time.monotonic()+1.5
            while True:
                state=subprocess.run(['/bin/ps','-o','stat=','-p',str(pid)],capture_output=True,text=True,timeout=1).stdout.strip()
                if not state or state.startswith('Z'):break
                assert time.monotonic()<deadline,'orphan still running'
                time.sleep(.05)
            assert len(list((root/'queue').glob('*.json')))==1
            assert json.loads((root/'queue'/name).read_text())==payload
            results.append({'mode':mode,'orphan_worker_stopped':True,'single_request_retained':True})
        finally:
            if parent.poll() is None:parent.kill();parent.wait(timeout=2)
print(json.dumps({'status':'passed','cases':results,'real_sends':0}))
