"""Compose immutable r3 from verified predecessor and current bounded API."""
import hashlib,json,zipfile
from pathlib import Path
old=Path('diagnostic-recovery-package-r2-20261002.zip')
assert hashlib.sha256(old.read_bytes()).hexdigest()=='76ddd54a77ae11952078415dae1a322a1434fbcf6df3e1bb42dd15031024efd9'
with zipfile.ZipFile(old) as archive:
    manifest=json.loads(archive.read('manifest.json'))
    contents={name:archive.read(name) for name in manifest['files']}
    for name,data in contents.items():assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
for name in ('HERALD/diagnostic_job_api.py','HERALD/diagnostic_request_bounds.py','validation/test_diagnostic_request_bounds.py','validation/test_diagnostic_http_worker.py'):
    contents[name]=Path(name.split('/')[-1]).read_bytes()
manifest['files']={name:hashlib.sha256(data).hexdigest() for name,data in contents.items()}
manifest['revision']=3
manifest['predecessor_sha256']=hashlib.sha256(old.read_bytes()).hexdigest()
target=Path('diagnostic-recovery-package-r3-20261002.zip')
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as archive:
    for name,data in contents.items():archive.writestr(name,data)
    archive.writestr('manifest.json',json.dumps(manifest,indent=2))
print(json.dumps({'files':len(contents),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
