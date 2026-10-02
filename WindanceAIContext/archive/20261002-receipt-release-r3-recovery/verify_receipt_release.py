"""Extract to a new isolated folder and verify exact archive/manifest inventory."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

archive=Path(sys.argv[1]);destination=Path(sys.argv[2]);expected=sys.argv[3]
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
destination.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(archive) as z:
    members=z.namelist()
    assert len(members)==len(set(members)) and all('/' not in n and '\\' not in n and n not in ('','.','..') for n in members)
    assert sum(info.file_size for info in z.infolist())<4*1024*1024
    z.extractall(destination)
manifest=json.loads((destination/'release-manifest.json').read_text())
assert set(members)==set(manifest)|{'release-manifest.json'}
for name,digest in manifest.items():assert hashlib.sha256((destination/name).read_bytes()).hexdigest()==digest,name
print(json.dumps({'status':'verified','files':len(manifest),'archive_sha256':expected,'production_changes':False}))
