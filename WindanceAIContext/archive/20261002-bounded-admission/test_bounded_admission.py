import fcntl,hashlib,json,tempfile,time
from pathlib import Path
from bounded_outbox_client import submit_and_wait
from keyed_outbox_status import lookup
from message_receipt_journal import Journal

results=[]
with tempfile.TemporaryDirectory(prefix='windance-admission-') as tmp:
    payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':False};key='synthetic'
    name='key-'+hashlib.sha256(key.encode()).hexdigest()+'.json'
    for case in ('fresh','busy','claim_only','orphan','journal_orphan','conflict','missing_journal','sms'):
        root=Path(tmp)/case;root.mkdir()
        for folder in ('claims','queue','results'):(root/folder).mkdir()
        if case!='missing_journal':Journal(root/'journal.db',create=True)
        fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if case in ('claim_only','conflict'):
            (root/'claims'/name).write_text(json.dumps({'content_sha256':fingerprint if case=='claim_only' else 'different'}))
        if case=='orphan':(root/'results'/name).write_text('{"ok":true}')
        if case=='journal_orphan':Journal(root/'journal.db').register(name[:-5],payload['to'],payload['chunks'])
        lock=(root/'claims'/name.replace('.json','.lock')).open('a')
        if case=='busy':fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        start=time.monotonic()
        result=submit_and_wait(root,key,dict(payload,sms=case=='sms'),seconds=.5)
        elapsed=time.monotonic()-start;lock.close()
        assert elapsed<1.5,(case,elapsed)
        if case=='fresh':
            assert result['reason']=='status_wait_expired',result
            assert lookup(root,key,payload)['status']=='pending'
            original=(root/'queue'/name).read_bytes()
            assert submit_and_wait(root,key,payload,seconds=.2)['status']=='unknown'
            assert (root/'queue'/name).read_bytes()==original
            assert len(list((root/'queue').glob('*.json')))==1
        else:
            assert not list((root/'queue').glob('*.json')),(case,result)
            expected={'busy':'admission_busy','claim_only':'claim_without_outcome','orphan':'orphaned_request_history','conflict':'request_content_mismatch','missing_journal':'admission_outcome_unknown','sms':'unsupported_admission'}
            expected['journal_orphan']='orphaned_request_history'
            assert result['reason']==expected[case],(case,result)
        results.append({'case':case,'status':result['status'],'seconds':round(elapsed,3)})
print(json.dumps({'status':'passed','cases':results,'real_sends':0}))
