import hashlib
import json
from pathlib import Path
import tempfile
from bounded_outbox_status import query
from message_receipt_journal import Journal

def tree_hash(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

results=[]
with tempfile.TemporaryDirectory() as tmp:
    for case in ('absent','claim_only','queued','inflight','quarantined','legacy','uncertain','conflict','forged_versioned','verified'):
        root=Path(tmp)/case;root.mkdir()
        payload={'to':'synthetic-owner','chunks':['PRIVATE_BODY'],'sms':False};key='synthetic-key'
        request_id='key-'+hashlib.sha256(key.encode()).hexdigest();name=request_id+'.json'
        for directory in ('claims','queue','inflight','uncertain','results'):(root/directory).mkdir()
        if case!='absent':
            fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            (root/'claims'/name).write_text(json.dumps({'content_sha256':'mismatch' if case=='conflict' else fingerprint}))
        if case in ('queued','inflight','quarantined'):
            folder={'queued':'queue','inflight':'inflight','quarantined':'uncertain'}[case]
            (root/folder/name).write_text('{}')
        if case=='legacy':(root/'results'/name).write_text('{"ok":true,"chunks":1}')
        if case=='uncertain':(root/'results'/name).write_text('{"ok":false,"status":"uncertain"}')
        if case in ('forged_versioned','verified'):
            (root/'results'/name).write_text('{"version":2,"ok":true,"status":"delivered","evidence":"local_messages_flags","chunks":1}')
        if case=='verified':
            j=Journal(root/'journal.db',create=True);j.register(request_id,payload['to'],payload['chunks'])
            snapshot={'status':'captured','store_id':'synthetic-store','boundary':1,'high_water':1,'anchor':'synthetic-anchor'}
            j.begin(request_id,0,'synthetic-store',1,snapshot)
            j.confirm(request_id,0,'synthetic-store',{'status':'delivered','evidence':'local_messages_flags','message_rowid':2})
        before=tree_hash(root)
        result=query(root,key,payload,seconds=0.4)
        assert tree_hash(root)==before,case
        expected={'absent':'unknown','claim_only':'unknown','queued':'unknown','inflight':'uncertain','quarantined':'uncertain',
                  'legacy':'legacy_submission','uncertain':'uncertain','conflict':'conflict','forged_versioned':'unavailable','verified':'verified_delivery'}[case]
        assert result['status']==expected,(case,result)
        if case=='queued':assert result['reason']=='status_wait_expired'
        assert 'PRIVATE_BODY' not in json.dumps(result) and 'synthetic-owner' not in json.dumps(result)
        results.append({'case':case,'status':result['status']})
print(json.dumps({'status':'passed','cases':results,'filesystem_unchanged':True,'sends':0}))

