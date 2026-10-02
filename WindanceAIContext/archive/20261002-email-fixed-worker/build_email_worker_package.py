"""Build a private fixed-worker package with verified local dependencies."""
import hashlib,json,shutil
from pathlib import Path
prior=Path('email-response-bound-private');root=Path('email-worker-package-private')
raw=(prior/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='1576629e12d6906dde9b9a0f207babbfb16ada9cb51395dff08fc5bc207443d0'
m=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
root.mkdir()
for n in m:shutil.copy2(prior/n,root/n)
for p in Path('email-worker-dependencies-private').glob('*.py'):shutil.copy2(p,root/p.name)
for n in ['email_fixed_worker.py','email_process_deadline.py']:shutil.copy2(n,root/n)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'files':len(manifest),'manifest_sha256':digest,'live_changes':False}))
