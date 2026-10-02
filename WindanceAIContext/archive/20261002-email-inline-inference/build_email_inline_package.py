"""Add unchanged live profile inference plus email-only inline adapter to private release."""
import hashlib,json,shutil
from pathlib import Path
prior=Path('email-service-layout-private');root=Path('email-inline-model-private')
raw=(prior/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d1fe484da171350fea87da13384c3be11f8a77a3c92c1aa01b1dfc9e6abf455a'
m=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
profile=Path('email-worker-dependencies-private/profile_inference.py');assert hashlib.sha256(profile.read_bytes()).hexdigest()=='df04658193555997fca45af682e578ab8756c265589e7d512ef347a81edf55cc'
root.mkdir()
for n in m:shutil.copy2(prior/n,root/n)
for name in ('herald_inference.py','profile_inference.py'):shutil.copy2(Path('email-worker-dependencies-private')/name,root/name)
shutil.copy2('email_inline_inference.py',root/'email_inline_inference.py')
p=root/'email_fixed_worker.py';s=p.read_text();anchor='    return module';assert s.count(anchor)==1
s=s.replace(anchor,'    from email_inline_inference import bind\n    bind(module)\n'+anchor);p.write_text(s)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'files':len(manifest),'manifest':digest,'profile_source_unchanged':True,'main':manifest['agent_harness.py']}))
