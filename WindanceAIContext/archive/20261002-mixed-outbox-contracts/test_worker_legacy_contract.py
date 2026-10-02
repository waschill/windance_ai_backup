import hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from receipt_request_worker import process_one,DAEMON_SHA256
source=Path(sys.argv[1]);assert hashlib.sha256(source.read_bytes()).hexdigest()==DAEMON_SHA256
spec=importlib.util.spec_from_file_location('legacy_host',source);host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
results=[]
with tempfile.TemporaryDirectory(prefix='windance-legacy-contract-') as tmp:
    for case in ('legacy_imessage','legacy_sms','unknown_contract','changed_body','lost_claim'):
        root=Path(tmp)/case;root.mkdir()
        for folder in ('claims','queue','results'):(root/folder).mkdir()
        host.ROOT=root;host.QUEUE=root/'queue';host.RESULTS=root/'results';host.LOG=root/'log'
        payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':case=='legacy_sms'}
        if case in ('changed_body','lost_claim'):payload['_receipt_contract']=2
        path=host.QUEUE/'request.json';path.write_text(json.dumps(payload));calls=[]
        if case in ('unknown_contract','changed_body'):
            (root/'claims/request.json').write_text(json.dumps({'receipt_contract':99 if case=='unknown_contract' else 2,'content_sha256':'mismatch'}))
        def run(command,**kwargs):
            assert command[0]=='/usr/bin/osascript' and command[-3]=='synthetic-owner'
            calls.append(command[-1]);return SimpleNamespace(returncode=0,stderr='')
        host.subprocess=SimpleNamespace(run=run)
        outcome=process_one(host,'request',root/'missing.db',root/'missing.whl',contract='auto')
        result=json.loads((host.RESULTS/'request.json').read_text())
        if case.startswith('legacy'):
            assert outcome=='processed_legacy' and result=={'ok':True,'chunks':1}
            assert calls==['true' if case=='legacy_sms' else 'false']
        else:assert outcome=='held' and result['status']=='uncertain' and not calls
        before=list(calls)
        assert process_one(host,'request',root/'missing.db',root/'missing.whl',contract='auto')=='request_absent' and calls==before
        results.append({'case':case,'outcome':outcome,'synthetic_transport_calls':len(calls)})
print(json.dumps({'status':'passed','cases':results,'legacy_not_upgraded':True,'real_sends':0}))
