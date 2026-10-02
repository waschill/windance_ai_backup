"""Build exact tested source package; no runtime configuration or secrets."""
import hashlib,json,zipfile
from pathlib import Path
pins={
'HERALD/diagnostic_job_api.py':'1847b0262438bcc51273a2a8824d99c5ce844ca8d1bc3d45b1994f9d7e915bfa',
'HERALD/diagnostic_job_ledger.py':'2c13c9529214bad626af66de33f469c750c78c9a8deb188d5043740f37920ee2',
'HERALD/diagnostic_remote_adapter.py':'f86cf92eaba56d15064bef6177d1cd1f3aaed84be1a19c680995f64741606883',
'AL/bounded_diagnosis_worker.py':'6cb4330b0d7281526bb27f0b85355b056968ce46bed83cc5df8001e98b6b35c9',
'AL/bounded_diagnosis_job_r4.py':'8631caa199085d4f437a89ad6fecfe5abf4d14c9911cd232e265a42ddddcb5c4',
'AL/diagnostic_remote_worker.py':'588c883babb0d0da30485ca8e507f78e7268ae9f800aacb69ae79ff619272d67',
'AL/diagnostic_cancel_worker.py':'5d44dad4c6910e51e2d689d59e329b318b0309939ec3f55ed41b826ef5b963fd',
'AL/inspect_diagnostic_record.py':'dc79ef7078fd52403dd1707fa794826445339fde21de248e5b24c889418f3f02',
'AL/failure.json':'1b8b6b3d5b4f7a7da751cfaf663d9fe894e4eeecb5cc51c31735704b395863a8'}
contents={}
for name,digest in pins.items():
    data=Path(name.split('/')[-1]).read_bytes()
    assert hashlib.sha256(data).hexdigest()==digest,(name,'Source differs from observed remote pin')
    contents[name]=data
test=Path('test_diagnostic_job_api.py').read_bytes()
contents['validation/test_diagnostic_job_api.py']=test
pins['validation/test_diagnostic_job_api.py']=hashlib.sha256(test).hexdigest()
metadata={'staged_only':True,'python':'3.11.15','dependencies':{'fastapi':'0.133.1','starlette':'1.3.1','pydantic':'2.13.4','uvicorn':'0.41.0','httpx':'0.28.1'},
          'docker_image':'sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f',
          'remote_path_dependency':'/tmp/windance-bounded-diagnosis-20261002','files':pins,
          'excluded':['credentials','operational database','service registration','Docker image bytes','production configuration']}
with zipfile.ZipFile('diagnostic-recovery-package-r2-20261002.zip','x',compression=zipfile.ZIP_DEFLATED) as archive:
    for name,data in contents.items():archive.writestr(name,data)
    archive.writestr('manifest.json',json.dumps(metadata,indent=2))
print(json.dumps({'files':len(pins),'zip_sha256':hashlib.sha256(Path('diagnostic-recovery-package-r2-20261002.zip').read_bytes()).hexdigest()}))
