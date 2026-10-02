"""Replace only the staged transport; verify the full predecessor manifest."""
import hashlib,json,shutil
from pathlib import Path
prior=Path('email-cached-transport-private');root=Path('email-response-bound-private')
m=json.loads((prior/'manifest.json').read_text())
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
assert m['gmail_single_attempt_transport.py']=='5753b6c3b9ac59021b2de6480656d167502d550e61254633aff09e4197a05c12'
root.mkdir()
for name in m:shutil.copy2(prior/name,root/name)
shutil.copy2('gmail_single_attempt_transport.py',root/'gmail_single_attempt_transport.py')
new={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
assert {n for n in m if m[n]!=new[n]}=={'gmail_single_attempt_transport.py'}
(root/'manifest.json').write_text(json.dumps(new,indent=2))
print(json.dumps({'files':len(new),'main':new['agent_harness.candidate.private.py'],
    'transport':new['gmail_single_attempt_transport.py'],'manifest_sha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()}))
