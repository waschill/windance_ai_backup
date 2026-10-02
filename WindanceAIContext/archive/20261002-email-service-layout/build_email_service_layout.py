"""Use production-compatible filenames in an inert private release directory."""
import hashlib,json,shutil
from pathlib import Path
prior=Path('email-bounded-entry-r2-private');root=Path('email-service-layout-private')
raw=(prior/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='2f1df84b255abf03c104a9930f3918ce3ea072de46e2b2adad91e81f25a544b0'
m=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
root.mkdir()
for name in m:shutil.copy2(prior/name,root/('agent_harness.py' if name=='agent_harness.candidate.private.py' else name))
p=root/'email_fixed_worker.py';p.write_text(p.read_text().replace("ROOT/'agent_harness.candidate.private.py'","ROOT/'agent_harness.py'"))
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'files':len(manifest),'manifest':digest,'main':manifest['agent_harness.py'],'worker':manifest['email_fixed_worker.py']}))
