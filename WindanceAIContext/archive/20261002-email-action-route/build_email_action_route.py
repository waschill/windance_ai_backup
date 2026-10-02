"""Stage route payload normalization without modifying stored approvals."""
import ast, hashlib, json, shutil
from pathlib import Path
src=Path('/Users/herald/backups/email-direct-rule-stop-20261002')
dst=Path('/Users/herald/backups/email-action-route-20261002')
m=json.loads((src/'manifest.json').read_text())
assert m['agent_harness.candidate.private.py']=='af8385aeba34d9a262424825769cc519132afe3f6b29976221d6984cfdf814af'
assert all(hashlib.sha256((src/n).read_bytes()).hexdigest()==v for n,v in m.items())
s=(src/'agent_harness.candidate.private.py').read_text(); tree=ast.parse(s)
f=next(n for n in tree.body if getattr(n,'name','')=='request_gmail_action')
old=ast.get_source_segment(s,f)
needle='    approval_payload = payload.model_dump(exclude_none=True)\n    approval_payload["action"] = normalized'
assert old.count(needle)==1
new=old.replace(needle,'    # Action identity belongs to the approval column, not its argument payload.\n    approval_payload = payload.model_dump(exclude_none=True, exclude={"action"})')
s=s.replace(old,new,1); after=ast.parse(s)
assert [ast.dump(n) for n in tree.body if n is not f]==[ast.dump(n) for n in after.body if getattr(n,'name','')!=f.name]
compile(s,'<staged-route>','exec'); dst.mkdir(mode=0o700,exist_ok=False)
for name in m: shutil.copy2(src/name,dst/name)
(dst/'agent_harness.candidate.private.py').write_text(s)
updated={n:hashlib.sha256((dst/n).read_bytes()).hexdigest() for n in m}
(dst/'manifest.json').write_text(json.dumps(updated,indent=2)+'\n')
print(json.dumps({'stage':str(dst),'candidate_sha256':updated['agent_harness.candidate.private.py'],'files':len(updated)}))
