import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);receipt=json.loads((root/'backup-receipt.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in receipt['files'].items())
(root/'hal-verification.json').write_text(json.dumps({'files':receipt['files']}))
print(json.dumps({'verified_files':len(receipt['files'])}))
