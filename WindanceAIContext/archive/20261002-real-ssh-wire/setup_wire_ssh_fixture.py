import hashlib,json
from pathlib import Path
from message_receipt_journal import Journal

root=Path('/tmp/windance-wire-ssh-20261002');root.mkdir(mode=0o700,exist_ok=False)
payload={'to':'synthetic-owner','chunks':['synthetic-private-body'],'sms':False};key='synthetic-wire-key'
request_id='key-'+hashlib.sha256(key.encode()).hexdigest();name=request_id+'.json'
for case in ('legacy','verified','queued'):
    folder=root/case;folder.mkdir()
    for child in ('claims','results','queue'):(folder/child).mkdir()
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (folder/'claims'/name).write_text(json.dumps({'content_sha256':fingerprint}))
    if case=='queued':(folder/'queue'/name).write_text(json.dumps(payload))
    if case=='legacy':(folder/'results'/name).write_text('{"ok":true,"chunks":1}')
    if case=='verified':
        j=Journal(folder/'journal.db',create=True);j.register(request_id,payload['to'],payload['chunks'])
        snapshot={'status':'captured','store_id':'synthetic-store','boundary':1,'high_water':1,'anchor':'synthetic-anchor'}
        j.begin(request_id,0,'synthetic-store',1,snapshot)
        j.confirm(request_id,0,'synthetic-store',{'status':'delivered','evidence':'local_messages_flags','message_rowid':2})
        (folder/'results'/name).write_text('{"version":2,"ok":true,"status":"delivered","evidence":"local_messages_flags","chunks":1}')
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
(root/'fixture-manifest.json').write_text(json.dumps(manifest))
print(json.dumps({'created_synthetic_fixture':str(root),'files':len(manifest),'production_changed':False}))
