"""Synthetic-only SAL fixture/probe; never references production outbox paths."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path('/tmp/windance-disconnect-20261002')
payload={'to':'synthetic-owner','chunks':['synthetic disconnect'],'sms':False};key='synthetic-disconnect'
name='key-'+hashlib.sha256(key.encode()).hexdigest()+'.json'
action=sys.argv[1]
if action=='prepare':
    from message_receipt_journal import Journal
    ROOT.mkdir(mode=0o700,exist_ok=False)
    for mode in ('query','submit'):
        root=ROOT/mode;root.mkdir()
        for folder in ('claims','queue','results'):(root/folder).mkdir()
        Journal(root/'journal.db',create=True)
        if mode=='query':
            fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            (root/'claims'/name).write_text(json.dumps({'content_sha256':fingerprint}))
            (root/'queue'/name).write_text(json.dumps(payload))
    print('{"prepared":true}')
elif action=='endpoint':
    mode=sys.argv[2];assert mode in ('query','submit');root=ROOT/mode
    (root/'endpoint.pid').write_text(str(os.getpid()))
    original=subprocess.Popen
    def spawn(*args,**kwargs):
        child=original(*args,**kwargs);(root/'worker.pid').write_text(str(child.pid));return child
    subprocess.Popen=spawn
    import outbox_protocol_cli
    sys.argv=['outbox_protocol_cli.py','--root',str(root),'--mode',mode,'--wait-seconds','2']
    raise SystemExit(outbox_protocol_cli.main())
elif action=='inspect':
    mode=sys.argv[2];assert mode in ('query','submit');root=ROOT/mode
    result={}
    for role in ('endpoint','worker'):
        path=root/(role+'.pid')
        state=subprocess.run(['/bin/ps','-o','stat=','-p',path.read_text()],capture_output=True,text=True,timeout=1).stdout.strip() if path.exists() else ''
        result[role+'_running']=bool(state and not state.startswith('Z'))
    files=list((root/'queue').glob('*.json'));result['queue_count']=len(files)
    result['queue_hashes']=[hashlib.sha256(p.read_bytes()).hexdigest() for p in files]
    print(json.dumps(result))
elif action=='cleanup':
    assert ROOT.resolve()==Path('/private/tmp/windance-disconnect-20261002')
    assert not any(p.is_symlink() for p in ROOT.rglob('*'))
    shutil.rmtree(ROOT);print('{"removed":true}')
else:raise SystemExit(2)
