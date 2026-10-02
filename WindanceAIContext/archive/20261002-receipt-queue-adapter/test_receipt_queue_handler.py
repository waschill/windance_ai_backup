"""Actual daemon file helpers + real staged queue/journal/coordinator, fake transport."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from message_receipt_journal import Journal
from receipt_chunk_coordinator import run_request
from receipt_queue_handler import handle


def child(source,root,phase):
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'
    spec=importlib.util.spec_from_file_location('host',source)
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    host.ROOT=root;host.QUEUE=root/'queue';host.RESULTS=root/'results';host.LOG=root/'log'
    def guard(event,args):
        if event in ('subprocess.Popen','os.system','os.posix_spawn') or event.startswith('socket.'):
            raise AssertionError('external_effect_attempted')
    sys.addaudithook(guard)
    effects=root/'effects'
    def send(recipient,text,sms):
        assert recipient=='synthetic-owner' and sms is False
        with effects.open('a') as f:f.write(text+'\n');f.flush();os.fsync(f.fileno())
    def capture():
        n=len(effects.read_text().splitlines()) if effects.exists() else 0
        return {'status':'captured','store_id':'synthetic-store','boundary':n,'high_water':n,'anchor':'synthetic-anchor'}
    def observe(recipient,text,boundary,snapshot):
        if phase=='unconfirmed':return {'status':'unconfirmed','reason':'delivery_flags_incomplete'}
        return {'status':'delivered','evidence':'local_messages_flags','message_rowid':boundary+1}
    def execute(j,request_id,recipient,chunks):
        return run_request(j,request_id,recipient,chunks,capture,observe,send)
    atomic=host.atomic_json
    def hooked(path,value):
        atomic(path,value)
        if phase=='after_marker' and path.parent.name=='inflight':os._exit(73)
        if phase=='after_result' and path.parent.name=='results':os._exit(73)
    host.atomic_json=hooked
    handle(host,root/'queue/request.json',root/'journal.db',execute)


def parent(source):
    results=[]
    with tempfile.TemporaryDirectory(prefix='windance-queue-receipt-') as tmp:
        for phase in ('normal','unconfirmed','legacy_marker','legacy_result','missing_journal','marker_without_history','after_marker','after_result','sms'):
            root=Path(tmp)/phase
            for name in ('queue','results','inflight'):(root/name).mkdir(parents=True,exist_ok=True)
            if phase!='missing_journal':Journal(root/'journal.db',create=True)
            payload={'to':'synthetic-owner','chunks':['chunk-one','chunk-two'],'sms':phase=='sms'}
            queue=root/'queue/request.json';queue.write_text(json.dumps(payload))
            if phase in ('legacy_marker','marker_without_history'):
                (root/'inflight/request.json').write_text(json.dumps({'request_id':'request','chunks_confirmed':0} if phase=='legacy_marker' else {'version':2,'request_id':'request'}))
            legacy=b'{"ok":true,"chunks":2}\n'
            if phase=='legacy_result':(root/'results/request.json').write_bytes(legacy)
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(source),str(root)]
            first=subprocess.run(command+[phase],capture_output=True,timeout=10)
            assert first.returncode==(73 if phase.startswith('after_') else 0),(phase,'first failed')
            count=lambda:len((root/'effects').read_text().splitlines()) if (root/'effects').exists() else 0
            before=count()
            # Resume only when queue remains: the actual daemon enumerates queue files.
            if queue.exists():
                second=subprocess.run(command+['resume'],capture_output=True,timeout=10)
                assert second.returncode==0,(phase,'restart failed')
            after=count()
            if phase=='after_marker':assert (before,after)==(0,2)
            else:assert after==before
            result=json.loads((root/'results/request.json').read_text())
            if phase in ('normal','after_marker','after_result'):
                assert after==2 and result['status']=='delivered' and result['version']==2
                assert not (root/'inflight/request.json').exists()
            elif phase=='legacy_result':assert after==0 and (root/'results/request.json').read_bytes()==legacy
            else:
                assert result['status']=='uncertain'
                assert (root/'uncertain/request.json').exists()
                assert after==(1 if phase=='unconfirmed' else 0)
            assert not queue.exists()
            results.append({'case':phase,'synthetic_sends':after,'legacy_result_preserved':phase=='legacy_result','status':result.get('status','legacy')})
    print(json.dumps({'status':'passed','cases':results,'real_sends':0,'production_changes':False}))


if __name__=='__main__':
    if sys.argv[1]=='--child':child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
    else:parent(Path(sys.argv[1]))
