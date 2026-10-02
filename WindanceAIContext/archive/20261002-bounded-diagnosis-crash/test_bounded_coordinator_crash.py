"""Kill the coordinator by injected os._exit; independently inspect exact container."""
import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
p=subprocess.run([sys.executable,str(root/'bounded_diagnosis_job_r2.py'),'crash-test'],capture_output=True,text=True,timeout=20)
assert p.returncode==73
job=Path(json.loads(p.stdout)['job'])
assert job.parent==root and job.name.startswith('job-')
identity=json.loads((job/'container.json').read_text());cid=identity['id']
start=time.monotonic()
try:
    while True:
        actual=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=5))[0]
        assert actual['Id']==cid and actual['Image']==identity['image']
        assert actual['Name']=='/'+identity['name']
        assert actual['Config']['Labels']['windance.diagnostic']=='isolated-r2'
        if not actual['State']['Running']: break
        assert time.monotonic()-start<7,'Independent deadline failed'
        time.sleep(0.1)
    assert actual['State']['ExitCode']==137
    assert not (job/'result.json').exists()
    record={'coordinator_exit':73,'worker_exit':137,'worker_stopped_verified':True,
            'elapsed_observation_seconds':round(time.monotonic()-start,3),
            'stale_recorded_status':json.loads((job/'status.json').read_text())[-1]['state'],
            'result_available':False,'interpretation':'Interrupted coordinator; bounded worker ended without accepted result. No replay.'}
    (root/'bounded-coordinator-crash-result.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record))
finally:
    subprocess.run(['docker','rm','-f','-v',cid],check=True,stdout=subprocess.DEVNULL,timeout=10)
