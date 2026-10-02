"""Fixed SSH operator endpoint for isolated tests; no server/listener."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from inspect_diagnostic_record import inspect
root=Path(__file__).resolve().parent
mode,key,evidence,worker,launcher=sys.argv[1:]
assert mode in ('run','reconcile') and re.fullmatch('[0-9a-f]{32}',key)
assert all(re.fullmatch('[0-9a-f]{64}',v) for v in (evidence,worker,launcher))
script=root/'bounded_diagnosis_job_r4.py'
assert hashlib.sha256(script.read_bytes()).hexdigest()==launcher
if mode=='run':
    p=subprocess.run([sys.executable,str(script),'diagnose',key,evidence,worker],capture_output=True,text=True,timeout=40)
    assert p.returncode==0
job=root/('job-'+key)
check=inspect(job);assert check['verification']=='verified_record' and check['recorded_outcome']=='completed'
terminal=json.loads((job/'terminal.json').read_text());m=json.loads((job/'input-manifest.json').read_text())
assert terminal['job_id']==key and m['failure.json']==evidence and m['bounded_diagnosis_worker.py']==worker
print(json.dumps({'job_id':key,'evidence_sha256':evidence,'worker_sha256':worker,
 'outcome':'completed','worker_stopped':True,'result':json.loads((job/'result.json').read_text()),
 'terminal_sha256':hashlib.sha256((job/'terminal.json').read_bytes()).hexdigest()}))
