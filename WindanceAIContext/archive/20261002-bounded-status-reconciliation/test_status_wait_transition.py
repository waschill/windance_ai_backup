import hashlib,json,tempfile,threading,time
from pathlib import Path
from bounded_outbox_status import query
from message_receipt_journal import Journal

with tempfile.TemporaryDirectory(prefix='windance-status-transition-') as tmp:
    root=Path(tmp);key='synthetic';payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':False}
    request_id='key-'+hashlib.sha256(key.encode()).hexdigest();name=request_id+'.json'
    for folder in ('claims','queue','results'):(root/folder).mkdir()
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (root/'claims'/name).write_text(json.dumps({'content_sha256':fingerprint}))
    (root/'queue'/name).write_text(json.dumps(payload))
    j=Journal(root/'journal.db',create=True);j.register(request_id,payload['to'],payload['chunks'])
    snapshot={'status':'captured','store_id':'synthetic-store','boundary':1,'high_water':1,'anchor':'synthetic-anchor'}
    j.begin(request_id,0,'synthetic-store',1,snapshot)
    j.confirm(request_id,0,'synthetic-store',{'status':'delivered','evidence':'local_messages_flags','message_rowid':2})
    def publish():
        temporary=root/'results/result.tmp'
        temporary.write_text(json.dumps({'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}))
        temporary.replace(root/'results'/name)
    timer=threading.Timer(.25,publish);timer.start()
    started=time.monotonic();result=query(root,key,payload,seconds=2);elapsed=time.monotonic()-started
    timer.join()
    assert result['status']=='verified_delivery',result
    assert .2<elapsed<2
    assert (root/'queue'/name).exists(),'query must never clean queue'
    before={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert query(root,key,payload,seconds=2)==result
    assert before=={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
print(json.dumps({'status':'passed','pending_to_verified_seconds':round(elapsed,3),'repeated_query_unchanged':True,'sends':0}))
