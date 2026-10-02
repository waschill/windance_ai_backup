import hashlib,json
from pathlib import Path
import sys
root=Path(sys.argv[1]);archive=Path(sys.argv[2])
manifest=json.loads((root/'release-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
assert hashlib.sha256(archive.read_bytes()).hexdigest()==sys.argv[3]
print(json.dumps({'verified_source_files':len(manifest),'archive_unchanged':True}))

