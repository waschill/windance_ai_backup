import hashlib,json
from pathlib import Path
import sys
root=Path(sys.argv[1]);archive=Path(sys.argv[2])
manifest=json.loads((root/'release-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='99a0ea538b950eab903662e7271e4cc53c77ee23b218656f87fa43aa7690b61d'
print(json.dumps({'verified_source_files':len(manifest),'archive_unchanged':True}))
