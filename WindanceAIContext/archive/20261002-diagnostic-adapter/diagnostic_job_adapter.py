"""Fixed local operator adapter. No listener or queue consumer; never retries a claim."""
import hashlib,json,subprocess,sys
from pathlib import Path
from inspect_diagnostic_record import inspect

def run_once(ledger,key,root,worker_sha256,launcher_sha256):
    root=Path(root)
    request,state=ledger.request(key)
    if state!='queued':return {'state':state,'started':False}
    if request['kind']!='email_payload_diagnosis':raise ValueError('Unsupported kind')
    launcher=root/'bounded_diagnosis_job_r4.py'
    if hashlib.sha256(launcher.read_bytes()).hexdigest()!=launcher_sha256:raise ValueError('Launcher drift')
    if hashlib.sha256((root/'bounded_diagnosis_worker.py').read_bytes()).hexdigest()!=worker_sha256:raise ValueError('Worker drift')
    if hashlib.sha256((root/'failure.json').read_bytes()).hexdigest()!=request['evidence_sha256']:raise ValueError('Evidence drift')
    if not ledger.claim(key):return {'state':'already_claimed','started':False}
    # Persisted claim precedes any worker start. Any failure leaves it held.
    p=subprocess.run([sys.executable,str(launcher),'diagnose',key,request['evidence_sha256'],worker_sha256],capture_output=True,text=True,timeout=45)
    if p.returncode:raise RuntimeError('Worker outcome unconfirmed; inspect existing job without retry')
    return reconcile_once(ledger,key,root,worker_sha256,started=True)

def reconcile_once(ledger,key,root,worker_sha256,*,started=False):
    """Accept existing exact terminal evidence only; no worker or Docker call."""
    root=Path(root);request,state=ledger.request(key)
    if state not in ('running','cancel_requested'):return {'state':state,'started':False}
    job=root/('job-'+key);checked=inspect(job)
    if checked['verification']!='verified_record' or checked['recorded_outcome']!='completed':raise RuntimeError('No accepted completion')
    terminal=json.loads((job/'terminal.json').read_text());manifest=json.loads((job/'input-manifest.json').read_text())
    if terminal['job_id']!=key or manifest['bounded_diagnosis_worker.py']!=worker_sha256 or manifest['failure.json']!=request['evidence_sha256']:raise RuntimeError('Completion binding mismatch')
    result=json.loads((job/'result.json').read_text())
    receipt={'job_id':key,'evidence_sha256':request['evidence_sha256'],'worker_sha256':worker_sha256,
             'outcome':'completed','worker_stopped':True,'result':result,
             'terminal_sha256':hashlib.sha256((job/'terminal.json').read_bytes()).hexdigest()}
    ledger.finish(key,receipt)
    return {'state':'completed','started':started}
