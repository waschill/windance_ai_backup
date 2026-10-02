"""Actual abrupt-process SQLite commit recovery, using synthetic effects only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from message_receipt_journal import Journal


def child(root,phase):
    j=Journal(root/'journal.db')
    permission=j.begin('request',0,'synthetic-store',10)
    if permission!='attempt_committed':return
    if phase=='after_attempt':os._exit(73)
    with (root/'effect').open('ab') as stream:
        stream.write(b'synthetic-send\n')
        stream.flush();os.fsync(stream.fileno())
    if phase=='after_effect':os._exit(73)
    j.submitted('request',0)
    if phase=='after_submission':os._exit(73)
    j.confirm('request',0,'synthetic-store',{'status':'delivered','evidence':'local_messages_flags','message_rowid':11})
    if phase=='after_receipt':os._exit(73)


def parent():
    results=[]
    with tempfile.TemporaryDirectory(prefix='windance-journal-crash-') as tmp:
        for phase in ('after_attempt','after_effect','after_submission','after_receipt'):
            root=Path(tmp)/phase;root.mkdir()
            j=Journal(root/'journal.db',create=True)
            j.register('request','synthetic-owner',['synthetic-body'])
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(root)]
            first=subprocess.run(command+[phase],capture_output=True,timeout=10)
            assert first.returncode==73,(phase,'expected_abrupt_exit')
            before=(root/'effect').read_bytes() if (root/'effect').exists() else b''
            second=subprocess.run(command+['resume'],capture_output=True,timeout=10)
            assert second.returncode==0,(phase,'restart_failed')
            after=(root/'effect').read_bytes() if (root/'effect').exists() else b''
            assert before==after,(phase,'effect_repeated')
            state=Journal(root/'journal.db').status('request')
            assert state['chunks']==[{'after_attempt':'attempting','after_effect':'attempting','after_submission':'submitted','after_receipt':'delivered'}[phase]]
            results.append({'phase':phase,'status':state['status'],'effects':len(after.splitlines()),'repeated':False})
    print(json.dumps({'status':'passed','cases':results,'real_messages':0,'power_loss_tested':False}))


if __name__=='__main__':
    if sys.argv[1:2]==['--child']:child(Path(sys.argv[2]),sys.argv[3])
    else:parent()
