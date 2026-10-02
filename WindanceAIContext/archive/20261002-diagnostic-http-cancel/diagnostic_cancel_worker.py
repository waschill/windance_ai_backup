"""Stop only the exact verified isolated diagnostic container for one job."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
key,evidence,worker=sys.argv[1:]
assert re.fullmatch('[0-9a-f]{32}',key) and all(re.fullmatch('[0-9a-f]{64}',s) for s in (evidence,worker))
job=root/('job-'+key);identity=json.loads((job/'container.json').read_text())
manifest=json.loads((job/'input-manifest.json').read_text())
assert manifest['failure.json']==evidence and manifest['bounded_diagnosis_worker.py']==worker
assert all(hashlib.sha256((job/'inputs'/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
cid=identity['id'];assert re.fullmatch('[0-9a-f]{64}',cid)
def inspect():
    return json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=3))[0]
actual=inspect()
assert actual['Id']==cid and actual['Name']=='/'+identity['name']
assert actual['Image']==identity['image']=='sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f'
assert actual['Config']['Labels']['windance.diagnostic']=='isolated-r2'
assert actual['HostConfig']['NetworkMode']=='none' and actual['HostConfig']['ReadonlyRootfs']
assert len(actual['Mounts'])==1
mount=actual['Mounts'][0]
assert mount['Source']==str(job/'inputs') and mount['Destination']=='/evidence' and mount['RW'] is False
assert actual['Config']['Entrypoint']==['timeout'] and actual['Config']['Cmd'][:2]==['--signal=KILL','3s']
if not actual['State']['Running']:
    raise RuntimeError('Worker already terminal; reconcile existing outcome without assigning a new cancellation cause')
subprocess.run(['docker','kill',cid],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=3)
actual=inspect()
assert actual['State']['Running'] is False and actual['State']['ExitCode']==137
print(json.dumps({'job_id':key,'evidence_sha256':evidence,'worker_sha256':worker,
                  'container_id':cid,'worker_stopped':True,'exit_code':137,'stop_acknowledged':True}))
