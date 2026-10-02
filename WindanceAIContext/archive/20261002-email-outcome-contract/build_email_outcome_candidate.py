"""Stage truthful report outcomes; no production import or mailbox effects."""
import ast,hashlib,json
from pathlib import Path
p=Path('/Users/herald/services/agent-harness/agent_harness.py');raw=p.read_bytes();s=raw.decode()
assert hashlib.sha256(raw).hexdigest()=='0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0'
t=ast.parse(s);n=next(n for n in t.body if getattr(n,'name','')=='gmail_autonomy_report');old=ast.get_source_segment(s,n);new=old
replacements=[
('        reason = choice["reason"]\n        try:', '        reason = choice["reason"]\n        action_attempted = False\n        try:'),
('                gmail_delete_message(str(item["id"]))','                action_attempted = True\n                trashed = gmail_delete_message(str(item["id"]))\n                if not isinstance(trashed, dict) or trashed.get("trashed") is not True or trashed.get("id") != str(item["id"]):\n                    raise RuntimeError("Unconfirmed Trash receipt")'),
('                    created = gmail_create_draft', '                    action_attempted = True\n                    created = gmail_create_draft'),
('                    draft_id = str(created.get("id") or "")','                    if not isinstance(created, dict) or created.get("draft_created") is not True or not isinstance(created.get("id"), str) or not created["id"].strip():\n                        raise RuntimeError("Unconfirmed draft receipt")\n                    draft_id = created["id"]'),
('            decision, action = "escalate", "error_left_untouched"\n            reason = f"Automatic action failed safely: {type(exc).__name__}: {str(exc)[:180]}"\n            lines.append(f"{ordinal}. ESCALATE — action failed; left for review: {sender} — {subject}")',
 '            decision = "escalate"\n            if action_attempted:\n                action = "action_outcome_unknown"\n                reason = "The mailbox action may have completed, but its result is unconfirmed. Reconcile before retrying or undoing it."\n                lines.append(f"{ordinal}. REVIEW — mailbox outcome unconfirmed: {sender} — {subject}")\n            else:\n                action = "error_before_action"\n                reason = "Preparation failed before this item reached a mailbox action."\n                lines.append(f"{ordinal}. ESCALATE — no mailbox action attempted: {sender} — {subject}")'),
('Nothing was sent. Escalated messages were not changed.', 'Nothing was sent by this report. Items marked untouched had no action attempted here; unconfirmed outcomes require reconciliation.')]
for a,b in replacements:
 assert new.count(a)==1,a[:50];new=new.replace(a,b)
candidate=s.replace(old,new)
assert [ast.dump(x) for x in t.body if getattr(x,'name','')!='gmail_autonomy_report']==[ast.dump(x) for x in ast.parse(candidate).body if getattr(x,'name','')!='gmail_autonomy_report']
root=Path('/Users/herald/backups/email-outcome-candidate-20261002');root.mkdir(mode=0o700,exist_ok=True)
target=root/'agent_harness.candidate.private.py';target.write_text(candidate);target.chmod(0o600)
print(json.dumps({'baseline_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changed_function':'gmail_autonomy_report','production_changes':False}))
