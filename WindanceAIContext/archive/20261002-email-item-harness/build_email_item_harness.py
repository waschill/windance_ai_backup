"""Wire durable original-item records through whole and selected batch calls."""
import ast,hashlib,json,shutil
from pathlib import Path
from email_approved_item_intent import SCHEMA
base=Path('/Users/herald/backups/email-action-receipts-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='46bd50849fd0c58ea8181de0e4fef0e6f2ec6074c4f4e29202899b6e3748de38'
s=p.read_text();candidate=s
for n in ast.parse(s).body:
 name=getattr(n,'name','');old=ast.get_source_segment(s,n) if name else ''
 if name=='db':
  a='CREATE INDEX IF NOT EXISTS email_action_intents_state ON email_action_intents(state);';assert old.count(a)==1;candidate=candidate.replace(old,old.replace(a,a+'\n'+SCHEMA))
 elif name=='execute_approved_action':
  new=old.replace('payload: dict[str, Any])','payload: dict[str, Any], *, approval_id: str | None = None, item_indexes: list[int] | None = None)')
  a=new.index('        results = []');b=new.index('    if action == "calendar.create":',a)
  new=new[:a]+'''        from email_approved_item_intent import perform as perform_item
        from email_approved_receipts import normalize
        actions = payload.get("actions", [])
        indexes = list(range(len(actions))) if item_indexes is None else item_indexes
        if not approval_id or not isinstance(actions, list) or not 1 <= len(actions) <= 50 or len(indexes) != len(actions) or len(set(indexes)) != len(indexes):
            raise RuntimeError("Bounded claimed batch identity required")
        results = []
        for expected, index in zip(actions, indexes):
            def execute_bound(recorded):
                if recorded != expected:
                    raise RuntimeError("Approved item payload changed")
                return execute_approved_action(recorded["action"], {k: v for k, v in recorded.items() if k != "action"})
            results.append(perform_item(db, approval_id, index, execute_bound, normalize))
        return {"action": action, "result": {"count": len(results), "items": results}}
''' +new[b:];candidate=candidate.replace(old,new)
 elif name=='approve_pending':
  a='execute_approved_action(approval["action"], payload)';assert old.count(a)==1;candidate=candidate.replace(old,old.replace(a,'execute_approved_action(approval["action"], payload, approval_id=approval["id"])'))
 elif name=='process_numbered_gmail_pin_decisions':
  a='execute_approved_action("gmail.batch", approved_payload)';assert old.count(a)==1;candidate=candidate.replace(old,old.replace(a,'execute_approved_action("gmail.batch", approved_payload, approval_id=approval["id"], item_indexes=selection["selected_indexes"])'))
excluded={'db','execute_approved_action','approve_pending','process_numbered_gmail_pin_decisions'}
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-item-harness-r2-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for f in base.iterdir():
 if f.suffix=='.py' and f.name!=p.name:shutil.copyfile(f,root/f.name);(root/f.name).chmod(0o600)
for name in ['email_approved_item_intent.py','email_approved_receipts.py','email_approval_lineage.py']:
 shutil.copyfile(Path('/tmp')/name,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
