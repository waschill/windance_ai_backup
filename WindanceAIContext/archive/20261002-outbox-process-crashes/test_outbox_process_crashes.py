"""Run actual daemon handle in disposable processes with sender intercepted.

All payloads are synthetic. Never runs the daemon main loop or Messages.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

EXPECTED='f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'


def child(source,root,phase):
    assert hashlib.sha256(source.read_bytes()).hexdigest()==EXPECTED
    spec=importlib.util.spec_from_file_location('outbox_under_test',source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT=root
    module.QUEUE=root/'queue'
    module.RESULTS=root/'results'
    module.LOG=root/'local.log'
    # Deny subprocess execution after importing the unchanged module.
    # Fake sender persists a synthetic side-effect receipt instead.
    def guard(event,args):
        if event in ('subprocess.Popen','os.system','os.posix_spawn') or event.startswith('socket.'):
            raise AssertionError('external_effect_attempted')
    sys.addaudithook(guard)
    def send(recipient,text,sms):
        assert recipient=='synthetic-owner' and text.startswith('synthetic chunk') and sms is False
        with (root/'synthetic_sends.jsonl').open('a') as stream:
            stream.write(json.dumps({'chunk':text})+'\n')
            stream.flush()
            os.fsync(stream.fileno())
        if phase=='after_send':os._exit(73)
    module.send_one=send
    original_atomic=module.atomic_json
    def atomic(path,value):
        original_atomic(path,value)
        if phase=='before_send' and path.parent.name=='inflight' and value['chunks_confirmed']==0:
            os._exit(73)
        if phase=='after_first_chunk_marker' and path.parent.name=='inflight' and value['chunks_confirmed']==1:
            os._exit(73)
        if phase=='after_result' and path.parent.name=='results':
            os._exit(73)
    module.atomic_json=atomic
    module.handle(root/'queue/request.json')


def parent(source):
    results=[]
    with tempfile.TemporaryDirectory(prefix='windance-outbox-crash-') as tmp:
        for phase in ('before_send','after_send','after_first_chunk_marker','after_result'):
            root=Path(tmp)/phase
            (root/'queue').mkdir(parents=True)
            (root/'results').mkdir()
            (root/'queue/request.json').write_text(json.dumps({'to':'synthetic-owner','chunks':['synthetic chunk 1','synthetic chunk 2'],'sms':False}))
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(source),str(root)]
            first=subprocess.run(command+[phase],capture_output=True,timeout=10)
            assert first.returncode==73,(phase,'expected_abrupt_exit')
            sent=root/'synthetic_sends.jsonl'
            count=lambda:len(sent.read_text().splitlines()) if sent.exists() else 0
            initial=count()
            assert initial=={'before_send':0,'after_send':1,'after_first_chunk_marker':1,'after_result':2}[phase]
            # Actual new interpreter resumes the surviving queue/marker/result files.
            second=subprocess.run(command+['resume'],capture_output=True,timeout=10)
            assert second.returncode==0,(phase,'resume_failed')
            assert count()==initial,(phase,'duplicate_send')
            result=json.loads((root/'results/request.json').read_text())
            if phase=='after_result':
                assert result=={'ok':True,'chunks':2}
                assert not (root/'inflight/request.json').exists()
            else:
                assert result['status']=='uncertain' and result['ok'] is False
                assert (root/'uncertain/request.json').exists()
                assert (root/'inflight/request.json').exists()
            assert not (root/'queue/request.json').exists()
            results.append({'phase':phase,'first_process_exit':73,'synthetic_effects':initial,'effects_after_restart':count(),
                            'outcome':'submitted_only' if phase=='after_result' else 'held_uncertain'})
    print(json.dumps({'status':'passed','source_sha256':EXPECTED,'cases':results,'actual_messages_sends':0,
                      'production_files_changed':False,'power_loss_tested':False}))


if __name__=='__main__':
    if sys.argv[1]=='--child':child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
    else:parent(Path(sys.argv[1]))
