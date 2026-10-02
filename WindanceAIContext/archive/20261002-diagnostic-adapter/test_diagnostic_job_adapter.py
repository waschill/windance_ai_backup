"""Actual ledger -> pinned Docker worker -> terminal receipt, plus lost local commit."""
import hashlib,json,sqlite3,sys,tempfile
from pathlib import Path
from diagnostic_job_ledger import Ledger
from diagnostic_job_adapter import run_once,reconcile_once
root=Path(__file__).resolve().parent
worker=sys.argv[1];launcher=sys.argv[2]
assert hashlib.sha256((root/'bounded_diagnosis_worker.py').read_bytes()).hexdigest()==worker
assert hashlib.sha256((root/'bounded_diagnosis_job_r4.py').read_bytes()).hexdigest()==launcher
evidence=hashlib.sha256((root/'failure.json').read_bytes()).hexdigest()
class Body:
    kind='email_payload_diagnosis';evidence_sha256=evidence
    def __init__(self,key):self.request_key=key
    def model_dump(self):return {'request_key':self.request_key,'kind':self.kind,'evidence_sha256':self.evidence_sha256}
results=[]
with tempfile.TemporaryDirectory() as folder:
    ledger=Ledger(Path(folder)/'jobs.db')
    for mode in ('normal','lost_receipt_commit'):
        body=Body(mode);key=ledger.submit('fixture-owner',body)['id']
        original=ledger.finish
        if mode=='lost_receipt_commit':
            def lost(*a,**k):raise RuntimeError('Simulated local receipt commit failure')
            ledger.finish=lost
        try:
            first=run_once(ledger,key,root,worker,launcher)
            assert mode=='normal' and first['started']
        except RuntimeError:
            assert mode=='lost_receipt_commit'
        finally:ledger.finish=original
        terminal=root/('job-'+key)/'terminal.json'
        before=hashlib.sha256(terminal.read_bytes()).hexdigest()
        again=run_once(ledger,key,root,worker,launcher)
        assert not again['started'] and hashlib.sha256(terminal.read_bytes()).hexdigest()==before
        if mode=='lost_receipt_commit':
            assert again['state']=='running'
            assert reconcile_once(ledger,key,root,worker)=={'state':'completed','started':False}
        assert ledger.result('fixture-owner',key)['result']['status']=='diagnosed'
        assert ledger.submit('fixture-owner',body)['id']==key
        results.append({'case':mode,'job':key,'terminal_sha256':before,'completed':True,'retry_started':False})
    with sqlite3.connect(ledger.path) as src,sqlite3.connect(Path(folder)/'cold.db') as dst:src.backup(dst)
    cold=Ledger(Path(folder)/'cold.db')
    for result in results:
        assert cold.result('fixture-owner',result['job'])==ledger.result('fixture-owner',result['job'])
        assert run_once(cold,result['job'],root,worker,launcher)['started'] is False
(root/'diagnostic-adapter-results.json').write_text(json.dumps({'cases':results,'cold_receipts_equal':True,'cold_retry_started':False},indent=2))
print((root/'diagnostic-adapter-results.json').read_text())
