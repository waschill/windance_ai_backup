"""Connect single approved Gmail operations to the same durable item journal."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-item-harness-r2-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='ed6c0ee54a67848807284cb25d0055d839f4646eb50083555bc89cd58b4e4481'
s=p.read_text();n=next(n for n in ast.parse(s).body if getattr(n,'name','')=='execute_approved_action');old=ast.get_source_segment(s,n)
a='    if action == "gateway.execute":'
b='''    if approval_id and action.startswith("gmail.") and action != "gmail.batch":
        from email_approved_item_intent import perform as perform_item
        from email_approved_receipts import normalize
        expected = {"action": action, **payload}
        def execute_single(recorded):
            if recorded != expected:
                raise RuntimeError("Approved single-action payload changed")
            return execute_approved_action(action, payload)
        return perform_item(db, approval_id, 0, execute_single, normalize)
''' +a
assert old.count(a)==1;candidate=s.replace(old,old.replace(a,b))
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','')!='execute_approved_action']==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','')!='execute_approved_action']
root=Path('/Users/herald/backups/email-single-intent-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for f in base.iterdir():
 if f.suffix=='.py' and f.name!=p.name:
  src=Path('/tmp/email_approved_item_intent.py') if f.name=='email_approved_item_intent.py' else f
  shutil.copyfile(src,root/f.name);(root/f.name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
