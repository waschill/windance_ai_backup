"""Stage sender-rule admission plus post-rule report refresh, no live mutation."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-bounded-history-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='2bfa3678156f7ee5d38eac01bf9e14e98d2370121d420a78fe65c2e624b2eb4f'
s=p.read_text();candidate=s
for n in ast.parse(s).body:
 if getattr(n,'name','')=='apply_email_sender_rules':
  old=ast.get_source_segment(s,n);new=old
  a='            gmail_delete_message(str(item["id"]))'
  b='            from email_action_intent import perform as mailbox_once\n            mailbox_once(db, "william", str(item["id"]), "trash", {}, lambda: gmail_delete_message(str(item["id"])))'
  assert new.count(a)==1;new=new.replace(a,b)
  a='            notices.append(f"- Tried to auto-delete {short_sender(item.get(\'from\', \'\'))}, but hit an error: {str(exc)[:160]}")'
  b='            notices.append("- A sender-rule action requires review; its mailbox outcome is not confirmed here. Do not repeat it without reconciliation.")'
  assert new.count(a)==1;new=new.replace(a,b)
  a='            audit("gmail_sender_rule_delete_error", {"sender": address, "message_id": item.get("id"), "error": str(exc)[:500]})'
  b='            audit("gmail_sender_rule_delete_error", {"reason": "action_or_receipt_unconfirmed"})'
  assert new.count(a)==1;new=new.replace(a,b);candidate=candidate.replace(old,new)
 elif getattr(n,'name','')=='gmail_autonomy_report':
  old=ast.get_source_segment(s,n)
  a='    items, explicit_rule_notices = apply_email_sender_rules(items)'
  b=a+'\n    journal = report_state(db, "william", [str(item.get("id") or "") for item in items])\n    prior_count += sum(operation_key("william", str(item.get("id") or "")) in journal["keys"] for item in items)\n    items = [item for item in items if operation_key("william", str(item.get("id") or "")) not in journal["keys"]]'
  assert old.count(a)==1;candidate=candidate.replace(old,old.replace(a,b))
exclude={'apply_email_sender_rules','gmail_autonomy_report'}
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in exclude]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in exclude]
root=Path('/Users/herald/backups/email-rule-intent-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for name in ['email_action_intent.py','gmail_draft_recovery.py']:shutil.copyfile(base/name,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
