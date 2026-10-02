"""Actual isolated worker must withhold unsupported diagnosis and repair."""
import hashlib,json,shutil,subprocess,sys,tempfile,uuid
from pathlib import Path
from inspect_diagnostic_record import inspect
root=Path(__file__).resolve().parent
original=json.loads((root/'failure.json').read_text())
cases=[('supported',original,True),('contradictory_effects',{**original,'after_synthetic_effects':0},False),
       ('missing_field',{k:v for k,v in original.items() if k!='journal_rejects_payload_action'},False),
       ('boolean_count',{**original,'before_synthetic_effects':False},False),
       ('invalid_source_hash',{**original,'before_sha256':'not-a-source-hash'},False)]
results=[]
for name,evidence,supported in cases:
    with tempfile.TemporaryDirectory() as folder:
        stage=Path(folder);stage.chmod(0o755)
        for n in ('bounded_diagnosis_worker.py','bounded_diagnosis_job_r4.py'):
            shutil.copy2(root/n,stage/n)
        (stage/'failure.json').write_text(json.dumps(evidence))
        hashes=[hashlib.sha256((stage/n).read_bytes()).hexdigest() for n in ('failure.json','bounded_diagnosis_worker.py')]
        p=subprocess.run([sys.executable,str(stage/'bounded_diagnosis_job_r4.py'),'diagnose',uuid.uuid4().hex,*hashes],capture_output=True,text=True,timeout=30)
        assert p.returncode==0,(name,p.stderr)
        job=Path(json.loads(p.stdout)['job']);result=json.loads((job/'result.json').read_text())
        assert result['status']==('diagnosed' if supported else 'insufficient_evidence'),name
        if not supported:assert result['cause'] is None and result['repair_proposal'] is None and result['rollback'] is None,name
        verified=inspect(job)
        assert verified['verification']=='verified_record' and verified['diagnostic_status']==result['status']
        results.append({'case':name,'status':result['status'],'unsupported_repair_withheld':not supported})
print(json.dumps({'cases':results,'actual_model_calls':0}))
