"""Discard real remote response, restore ledger, reconcile in a fresh process."""
import hashlib,json,sqlite3,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
from diagnostic_job_ledger import Ledger
from diagnostic_remote_adapter import run_once,collect

if sys.argv[1]=='recover':
    _,_,database,key,worker,launcher=sys.argv
    print(json.dumps(collect(Ledger(database),key,worker,launcher)))
    raise SystemExit(0)

worker,launcher,evidence=sys.argv[1:]
class Body:
    request_key='remote-response-loss'
    def model_dump(self):return {'request_key':self.request_key,'kind':'email_payload_diagnosis','evidence_sha256':evidence}
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);ledger=Ledger(root/'jobs.db');key=ledger.submit('fixture-owner',Body())['id']
    real_run=subprocess.run;remote_receipt={};attempts=[]
    def discard_response(args,**kwargs):
        attempts.append(args)
        p=real_run(args,**kwargs)
        assert p.returncode==0
        remote_receipt.update(json.loads(p.stdout))
        raise subprocess.TimeoutExpired('simulated_lost_remote_response',50)
    with patch('diagnostic_remote_adapter.subprocess.run',side_effect=discard_response):
        try:run_once(ledger,key,worker,launcher)
        except subprocess.TimeoutExpired:pass
        else:raise AssertionError('Loss was not injected')
    assert len(attempts)==1 and ledger.request(key)[1]=='running'
    assert run_once(ledger,key,worker,launcher)=={'started':False,'state':'running'}
    with sqlite3.connect(ledger.path) as source,sqlite3.connect(root/'cold.db') as target:source.backup(target)
    restored=Ledger(root/'cold.db')
    try:collect(restored,key,'0'*64,launcher)
    except RuntimeError:pass
    else:raise AssertionError('Wrong worker version accepted')
    assert restored.request(key)[1]=='running'
    recovered=real_run([sys.executable,__file__,'recover',str(root/'cold.db'),key,worker,launcher],capture_output=True,text=True,timeout=20)
    assert recovered.returncode==0,recovered.stderr
    assert json.loads(recovered.stdout)=={'started':False,'state':'completed'}
    final=restored.result('fixture-owner',key)
    assert final==remote_receipt
    assert run_once(restored,key,worker,launcher)=={'started':False,'state':'completed'}
    summary={'job_id':key,'actual_remote_completion_before_injected_loss':True,
             'held_state_before_recovery':'running','duplicate_start_denied':True,
             'wrong_worker_version_denied':True,'cold_fresh_process_reconciled':True,
             'receipt_exactly_matches_original':True,'recovery_started_worker':False,
             'terminal_sha256':final['terminal_sha256']}
Path('/tmp/diagnostic-remote-loss-results.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
