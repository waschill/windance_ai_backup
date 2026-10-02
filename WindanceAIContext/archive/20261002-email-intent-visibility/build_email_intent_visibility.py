"""Exclude recorded operations before rules/model work; retain held counts."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-intent-candidate-20261002/agent_harness.candidate.private.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='365299e32e4d65626db2d1f277f450bd37c4f89bffaba3beebaa275770c3b192'
s=base.read_text();t=ast.parse(s);node=next(n for n in t.body if getattr(n,'name','')=='gmail_autonomy_report');old=ast.get_source_segment(s,node);new=old
pairs=[
('    items = recent_inbox_email(limit=max(1, min(limit, 50)), include_body=True)',
 '    from email_action_intent import report_state, operation_key\n    journal = report_state(db, "william")\n    items = recent_inbox_email(limit=max(1, min(limit, 50)), include_body=True)\n    prior_count = sum(operation_key("william", str(item.get("id") or "")) in journal["keys"] for item in items)\n    items = [item for item in items if operation_key("william", str(item.get("id") or "")) not in journal["keys"]]'),
('    if not pending and not explicit_rule_notices:', '    if not pending and not explicit_rule_notices and not journal["unconfirmed"] and not prior_count:'),
('    lines = ["Email authority report", ""]',
 '    lines = ["Email authority report", ""]\n    if journal["unconfirmed"]:\n        lines.append(f"REVIEW: {journal[\'unconfirmed\']} previously attempted mailbox operation(s) remain unconfirmed, including items no longer in this inbox view. Reconcile before retrying.")\n    if prior_count:\n        lines.append(f"{prior_count} inbox message(s) already have durable action records; no new classification, draft or mailbox action was attempted for them.")')]
for a,b in pairs:assert new.count(a)==1;new=new.replace(a,b)
candidate=s.replace(old,new)
assert [ast.dump(n) for n in t.body if getattr(n,'name','')!='gmail_autonomy_report']==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','')!='gmail_autonomy_report']
root=Path('/Users/herald/backups/email-intent-visibility-20261002');root.mkdir(mode=0o700,exist_ok=True)
target=root/'agent_harness.candidate.private.py';target.write_text(candidate);target.chmod(0o600)
shutil.copyfile('/tmp/email_action_intent.py',root/'email_action_intent.py');(root/'email_action_intent.py').chmod(0o600)
print(json.dumps({'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'journal_sha256':hashlib.sha256((root/'email_action_intent.py').read_bytes()).hexdigest(),'production_changes':False}))
