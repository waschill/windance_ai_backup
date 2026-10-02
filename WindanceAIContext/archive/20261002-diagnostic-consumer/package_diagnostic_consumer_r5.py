"""Preserve verified r3 and add bounded transport sources/test."""
import hashlib,json,zipfile
from pathlib import Path
prior=Path('diagnostic-recovery-package-r4-20261002.zip')
assert hashlib.sha256(prior.read_bytes()).hexdigest()=='a7797198f78d02a021715f00b5ac9aa041366863e19d67357281938f51e1a15b'
with zipfile.ZipFile(prior) as archive:
    manifest=json.loads(archive.read('manifest.json'));contents={k:archive.read(k) for k in manifest['files']}
    for name,data in contents.items():assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
for name in ('HERALD/diagnostic_job_ledger.py','HERALD/diagnostic_consumer.py','validation/test_diagnostic_admission.py','validation/test_diagnostic_consumer.py','validation/test_diagnostic_consumer_http.py'):
    contents[name]=Path(name.split('/')[-1]).read_bytes()
manifest.update(revision=5,predecessor_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),files={k:hashlib.sha256(v).hexdigest() for k,v in contents.items()})
out=Path('diagnostic-recovery-package-r5-20261002.zip')
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as archive:
    for k,v in contents.items():archive.writestr(k,v)
    archive.writestr('manifest.json',json.dumps(manifest,indent=2))
print(json.dumps({'files':len(contents),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))

