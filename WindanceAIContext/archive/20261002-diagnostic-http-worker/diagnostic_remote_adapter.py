"""Fixed HERALD-to-AL diagnostic adapter. Trusted operator configuration only."""
import json,subprocess
def run_once(ledger,key,worker_hash,launcher_hash):
    request,state=ledger.request(key)
    if state!='queued':return {'started':False,'state':state}
    if request['kind']!='email_payload_diagnosis':raise ValueError('Unsupported job kind')
    if not ledger.claim(key):return {'started':False,'state':'already_claimed'}
    return collect(ledger,key,worker_hash,launcher_hash,mode='run')
def collect(ledger,key,worker_hash,launcher_hash,*,mode='reconcile'):
    import re
    request,state=ledger.request(key)
    if state not in ('running','cancel_requested'):return {'started':False,'state':state}
    if mode not in ('run','reconcile') or not re.fullmatch('[0-9a-f]{32}',key):raise ValueError('Bounded identity required')
    values=[request['evidence_sha256'],worker_hash,launcher_hash]
    if any(not re.fullmatch('[0-9a-f]{64}',v) for v in values):raise ValueError('Exact hashes required')
    # Arguments are only fixed words and validated hex; no request text enters SSH shell.
    args=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','AL','python3',
          '/tmp/windance-bounded-diagnosis-20261002/diagnostic_remote_worker.py',mode,key,*values]
    p=subprocess.run(args,capture_output=True,text=True,timeout=50)
    if p.returncode or len(p.stdout)>65536:raise RuntimeError('Remote outcome unconfirmed; inspect existing job, never replay')
    receipt=json.loads(p.stdout)
    if receipt.get('worker_sha256')!=worker_hash:raise RuntimeError('Worker version mismatch')
    ledger.finish(key,receipt)
    return {'started':mode=='run','state':'completed'}
