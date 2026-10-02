import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from outbox_wire_protocol import parse_response

with tempfile.TemporaryDirectory(prefix='windance-wire-endpoint-') as tmp:
    root=Path(tmp);(root/'claims').mkdir();(root/'results').mkdir()
    key='synthetic';payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':False}
    name='key-'+hashlib.sha256(key.encode()).hexdigest()+'.json'
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (root/'claims'/name).write_text(json.dumps({'content_sha256':digest}))
    (root/'results'/name).write_text('{"ok":true,"chunks":1}')
    before={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    results=[]
    for mode in ('query','submit'):
        child=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('outbox_protocol_cli.py')),
                              '--root',str(root),'--mode',mode],
                             input=json.dumps({'key':key,'payload':payload}),text=True,capture_output=True,timeout=3)
        assert child.returncode==12,(child.returncode,child.stderr)
        assert parse_response(child.stdout,child.returncode,key,payload)=={'status':'legacy_submission'}
        assert before=={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        results.append({'mode':mode,'exit_code':child.returncode,'legacy_not_upgraded':True})
print(json.dumps({'status':'passed','cases':results,'sends':0,'files_unchanged':True}))
