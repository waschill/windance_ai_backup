"""Verify timeout kills an ordinary same-group child, no real sender."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from bounded_outbox_request import run_bounded

with tempfile.TemporaryDirectory(prefix='windance-group-bound-') as tmp:
    root=Path(tmp)
    worker=root/'worker.py'
    worker.write_text('''import subprocess,sys,time
from pathlib import Path
root=Path(__file__).parent
program="import os,time; from pathlib import Path; root=Path("+repr(str(root))+"); (root/'descendant.pid').write_text(str(os.getpid())); time.sleep(2); (root/'late_effect').write_text('synthetic'); time.sleep(60)"
subprocess.Popen([sys.executable,'-c',program])
time.sleep(60)
''')
    result=run_bounded([sys.executable,str(worker)],seconds=0.75)
    assert result=={'status':'uncertain','reason':'whole_request_deadline'}
    pid=int((root/'descendant.pid').read_text())
    state=subprocess.run(['/bin/ps','-o','stat=','-p',str(pid)],capture_output=True,text=True,timeout=1)
    assert not state.stdout.strip() or state.stdout.strip().startswith('Z'),state.stdout
    time.sleep(2.1)
    assert not (root/'late_effect').exists()
print(json.dumps({'status':'passed','same_group_descendant_not_running':True,'late_synthetic_effect_absent':True,'escaped_sessions_tested':False}))
