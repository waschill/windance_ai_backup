import hashlib, json
from pathlib import Path
from urllib.request import Request, urlopen
dest=Path('/Users/zuzu/services/maintenance-recovery-20260924/node--26.8.1.arm64_tahoe.bottle.tar.gz')
digest='489838f28f1131c8555ea7b61fffbb4f957c8a20a4731d2305869084fb864db4'
with urlopen('https://ghcr.io/token?service=ghcr.io&scope=repository:homebrew/core/node:pull') as r:
    token=json.load(r)['token']
req=Request('https://ghcr.io/v2/homebrew/core/node/blobs/sha256:'+digest,headers={'Authorization':'Bearer '+token})
with urlopen(req) as r:
    blob=r.read()
if hashlib.sha256(blob).hexdigest()!=digest:
    raise SystemExit('Digest verification failed')
dest.write_bytes(blob)
print('Verified official Homebrew Node 26.8.1 rollback bottle')
