"""Compose bounded history query into exact retained private candidate."""
import ast, hashlib, json, shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-recoverable-candidate-20261002')
p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='0f04b4a436e2f9ea46f8545222d333ce5abe86f3be7aba43e22d2f1b7de4a1f9'
s=p.read_text();candidate=s
a='    journal = report_state(db, "william")\n    items = recent_inbox_email(limit=max(1, min(limit, 50)), include_body=True)'
b='    items = recent_inbox_email(limit=max(1, min(limit, 50)), include_body=True)\n    journal = report_state(db, "william", [str(item.get("id") or "") for item in items])'
assert candidate.count(a)==1;candidate=candidate.replace(a,b)
a=' reconciled_at TEXT);';b=a+'\nCREATE INDEX IF NOT EXISTS email_action_intents_state ON email_action_intents(state);'
assert candidate.count(a)==1;candidate=candidate.replace(a,b)
excluded={'db','gmail_autonomy_report'}
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-bounded-history-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for source,name in [(Path('/tmp/email_action_intent.py'),'email_action_intent.py'),(base/'gmail_draft_recovery.py','gmail_draft_recovery.py')]:
    shutil.copyfile(source,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
