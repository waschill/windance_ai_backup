"""Offline private archive verification/restoration; does not import backed-up code."""
import hashlib,json
from pathlib import Path,PurePosixPath
import sys,zipfile

archive=Path(sys.argv[1]);destination=Path(sys.argv[2]);expected=sys.argv[3]
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
destination.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(archive) as z:
    names=z.namelist()
    assert len(names)==len(set(names))
    for name in names:
        p=PurePosixPath(name)
        assert not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name
        assert name=='private-manifest.json' or p.parts[0] in ('code','state')
    assert sum(i.file_size for i in z.infolist())<34*1024*1024
    z.extractall(destination)
manifest=json.loads((destination/'private-manifest.json').read_text())
assert set(names)==set(manifest)|{'private-manifest.json'}
counts={}
for name,digest in manifest.items():
    path=destination/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    if name.startswith('state/'):
        value=json.loads(path.read_text())
        assert type(value) is dict
        folder=PurePosixPath(name).parts[1];counts[folder]=counts.get(folder,0)+1
print(json.dumps({'status':'verified_offline_restore','files':len(manifest),'state_counts':counts,
                  'archive_sha256':expected,'code_executed':False,'sends':0}))
