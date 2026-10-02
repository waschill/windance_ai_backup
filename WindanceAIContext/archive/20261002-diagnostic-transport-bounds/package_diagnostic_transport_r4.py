"""Preserve verified r3 and add bounded transport sources/test."""
import hashlib,json,zipfile
from pathlib import Path
prior=Path('diagnostic-recovery-package-r3-20261002.zip')
assert hashlib.sha256(prior.read_bytes()).hexdigest()=='760766df5bcb81805632203f6cf2cf5cc4dc13e804e6a2ad164bc12ee898b447'
with zipfile.ZipFile(prior) as archive:
    manifest=json.loads(archive.read('manifest.json'));contents={k:archive.read(k) for k in manifest['files']}
    for name,data in contents.items():assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
for name in ('HERALD/diagnostic_remote_adapter.py','HERALD/diagnostic_bounded_process.py','validation/test_diagnostic_bounded_process.py'):
    contents[name]=Path(name.split('/')[-1]).read_bytes()
manifest.update(revision=4,predecessor_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),files={k:hashlib.sha256(v).hexdigest() for k,v in contents.items()})
out=Path('diagnostic-recovery-package-r4-20261002.zip')
with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as archive:
    for k,v in contents.items():archive.writestr(k,v)
    archive.writestr('manifest.json',json.dumps(manifest,indent=2))
print(json.dumps({'files':len(contents),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
