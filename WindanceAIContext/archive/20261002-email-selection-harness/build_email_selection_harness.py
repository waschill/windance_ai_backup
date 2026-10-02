"""Compose selection claim into exact private Harness schema and handler."""
import ast,hashlib,json,shutil
from pathlib import Path
from email_approval_selection import SCHEMA
base=Path('/Users/herald/backups/email-approval-claim-r2-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='96ceb3e4abe378d4bcf3648d68e810044aabf79c16bbbe78b0a42d5411690892'
s=p.read_text();candidate=s
for n in ast.parse(s).body:
 if getattr(n,'name','')=='db':
  old=ast.get_source_segment(s,n);a='CREATE INDEX IF NOT EXISTS email_action_intents_state ON email_action_intents(state);'
  assert old.count(a)==1;candidate=candidate.replace(old,old.replace(a,a+'\n'+SCHEMA))
 elif getattr(n,'name','')=='process_numbered_gmail_pin_decisions':
  old=ast.get_source_segment(s,n);new=old
  a='    decisions: list[tuple[int, str]] = []';assert new.count(a)==1;new=new.replace(a,'    require_william_mailbox()\n'+a)
  start=new.index('    if remaining_actions:\n');end=new.index('    if not approved_actions:\n',start)
  replacement='''    from email_approval_selection import claim as claim_selection, SelectionHeld
    selected_indexes = [i for i, item in enumerate(payload.get("actions", [])) if by_message.get(str(item.get("message_id"))) == "approve"]
    rejected_indexes = [i for i, item in enumerate(payload.get("actions", [])) if by_message.get(str(item.get("message_id"))) == "reject"]
    try:
        selection = claim_selection(db, approval, selected_indexes, rejected_indexes, approval_is_fresh, now)
    except (SelectionHeld, ValueError):
        return "This approval expired, changed or is already being handled. No selected action was repeated; review its existing status.", "deterministic", "approval-held"
'''
  new=new[:start]+replacement+new[end:]
  a='        response = f"Approved and executed {len(approved_actions)} selected email action(s)."'
  assert new.count(a)==1;new=new.replace(a,a+'\n        final_status = "executed"')
  a='''        audit("gmail_numbered_pin_decision_failed", {"id": approval["id"], "error": str(exc)[:500]})
        response = f"The selected approval was accepted, but execution failed: {str(exc)[:300]}"'''
  b='''        audit("gmail_numbered_pin_decision_failed", {"id": approval["id"], "reason": "execution_outcome_unconfirmed"})
        response = "The selected approval was accepted, but its mailbox outcome is unconfirmed. Do not repeat it until reconciled."
        final_status = "uncertain"
    with db() as conn:
        changed = conn.execute("UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=? AND status='executing'", (final_status, now(), "Selected batch outcome: " + final_status, approval["id"])).rowcount
        if changed != 1:
            conn.rollback()
            raise RuntimeError("Selected approval status changed before receipt; reconcile before retrying")
        conn.commit()'''
  assert new.count(a)==1;new=new.replace(a,b);candidate=candidate.replace(old,new)
excluded={'db','process_numbered_gmail_pin_decisions'}
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-selection-harness-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for name in ['email_action_intent.py','gmail_draft_recovery.py','email_approval_selection.py']:
 src=Path('/tmp')/name if name=='email_approval_selection.py' else base/name
 shutil.copyfile(src,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
