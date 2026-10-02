"""Real local processes test caps/deadlines; adapter uncertainty uses fixed fixture."""
import json,sys,tempfile,time
from pathlib import Path
from diagnostic_bounded_process import capture
from diagnostic_job_ledger import Ledger
from diagnostic_job_api import Submission
import diagnostic_remote_adapter as adapter

def run(code,**kwargs):return capture([sys.executable,'-c',code],timeout=kwargs.pop('timeout',2),max_stdout=64,max_stderr=32,**kwargs)
assert run('print("ok")')=='ok\n'
assert run('import os;os.write(1,b"x"*64)')=='x'*64
cases=[('import os;os.write(1,b"x"*65)',2),('import os;os.write(2,b"PRIVATE_SENTINEL"*9)',2),('import time;time.sleep(5)',.05),('import os;os.write(1,b"\\xff")',2),('raise SystemExit(3)',2)]
for code,timeout in cases:
    start=time.monotonic()
    try:run(code,timeout=timeout);raise AssertionError('Expected rejection')
    except RuntimeError as exc:assert 'PRIVATE_SENTINEL' not in str(exc) and 'unconfirmed' in str(exc)
    assert time.monotonic()-start<3
with tempfile.TemporaryDirectory() as directory:
    ledger=Ledger(Path(directory)/'jobs.db')
    body=Submission(request_key='bounded-loss',kind='email_payload_diagnosis',evidence_sha256='a'*64)
    key=ledger.submit('owner',body)['id']
    calls=[]
    def fail(*args,**kwargs):calls.append(1);raise RuntimeError('Transport output exceeds bound; outcome unconfirmed')
    adapter.capture=fail
    try:adapter.run_once(ledger,key,'b'*64,'c'*64);raise AssertionError('Expected uncertainty')
    except RuntimeError:pass
    assert ledger.request(key)[1]=='running'
    assert adapter.run_once(ledger,key,'b'*64,'c'*64)=={'started':False,'state':'running'}
    assert len(calls)==1
print(json.dumps({'status':'passed','real_process_cases':7,'uncertain_job_not_replayed':True,'remote_worker_calls':0}))
