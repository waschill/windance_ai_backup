import fcntl,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
source=Path(sys.argv[1]);results=[]
with tempfile.TemporaryDirectory(prefix='windance-dispatcher-') as tmp:
    for case in ('idle','dispatcher_busy','legacy_owner_busy','legacy_result','missing_journal'):
        root=Path(tmp)/case;root.mkdir()
        for folder in ('queue','results','claims'):(root/folder).mkdir()
        payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':False}
        if case=='missing_journal':
            fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            (root/'claims/request.json').write_text(json.dumps({'content_sha256':fingerprint,'receipt_contract':2}))
            payload['_receipt_contract']=2
        if case!='idle':(root/'queue/request.json').write_text(json.dumps(payload))
        if case in ('legacy_owner_busy','legacy_result'):(root/'results/request.json').write_text('{"ok":true,"chunks":1}')
        lock=None
        if case in ('dispatcher_busy','legacy_owner_busy'):
            lock=(root/('dispatcher.lock' if case=='dispatcher_busy' else 'owner.lock')).open('a')
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        command=[sys.executable,'-B',str(Path(__file__).with_name('receipt_outbox_dispatcher.py')),
                 '--root',str(root),'--source',str(source),'--database',str(root/'unused.db'),
                 '--wheel',str(root/'unused.whl'),'--request-seconds','2','--once']
        try:r=subprocess.run(command,capture_output=True,text=True,timeout=5)
        finally:
            if lock:lock.close()
        assert r.returncode==(75 if case=='dispatcher_busy' else 0),(case,r.returncode)
        outcome=json.loads(r.stdout) if r.stdout else {'status':'dispatcher_busy'}
        if case=='legacy_owner_busy':assert outcome=={'status':'process_exited','returncode':75} and (root/'queue/request.json').exists()
        if case=='legacy_result':assert not (root/'queue/request.json').exists() and (root/'results/request.json').read_text()=='{"ok":true,"chunks":1}'
        if case=='missing_journal':assert json.loads((root/'results/request.json').read_text())['status']=='uncertain' and (root/'uncertain/request.json').exists()
        if case=='dispatcher_busy':assert (root/'queue/request.json').exists() and not list((root/'results').iterdir())
        if case=='idle':assert outcome=={'status':'idle'}
        results.append({'case':case,'outcome':outcome})
print(json.dumps({'status':'passed','cases':results,'real_sends':0,'service_registered':False}))
