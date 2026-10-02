"""Private actual-Harness candidate with prepared MIME and atomic evidence."""
import ast,hashlib,json,shutil
from pathlib import Path
from email_action_intent import SCHEMA
base=Path('/Users/herald/backups/email-intent-visibility-20261002/agent_harness.candidate.private.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='4fb5bc825bc95e5fbfa5e6c68ac2fb0afab9b6ba9a6bcb0e71fb357c7772e19c'
s=base.read_text();tree=ast.parse(s);candidate=s
for node in tree.body:
 if getattr(node,'name','')=='db':
  old=ast.get_source_segment(s,node);a=old.index('CREATE TABLE IF NOT EXISTS email_action_intents (');b=old.index('confirmed_at TEXT);',a)+len('confirmed_at TEXT);')
  candidate=candidate.replace(old,old[:a]+SCHEMA+old[b:])
 elif getattr(node,'name','')=='gmail_autonomy_report':
  old=ast.get_source_segment(s,node)
  anchor='created = mailbox_once(db, "william", str(item["id"]), "draft", {"to": address, "subject": draft_subject, "body": body, "thread_id": item.get("thread_id")}, lambda: gmail_create_draft(address, draft_subject, body, item.get("thread_id")))'
  replacement='from email_action_intent import perform_recoverable_draft\n                    created = perform_recoverable_draft(db, "william", str(item["id"]), {"to": address, "subject": draft_subject, "body": body, "thread_id": item.get("thread_id")}, _gmail_create_prepared_draft)'
  assert old.count(anchor)==1;candidate=candidate.replace(old,old.replace(anchor,replacement))
helper='''def _gmail_create_prepared_draft(raw: str, thread_id: str | None) -> dict[str, Any]:
    """Internal prepared MIME path; the durable journal owns retries."""
    require_william_mailbox()
    message = {"raw": raw}
    if thread_id:
        message["threadId"] = thread_id
    result = gmail_service().users().drafts().create(userId="me", body={"message": message}).execute(num_retries=0)
    if not isinstance(result, dict) or not isinstance(result.get("id"), str) or not result["id"].strip():
        raise RuntimeError("Unconfirmed draft receipt")
    return {"draft_created": True, "id": result["id"]}


'''
assert candidate.count('def gmail_create_draft(')==1;candidate=candidate.replace('def gmail_create_draft(',helper+'def gmail_create_draft(')
excluded={'db','gmail_autonomy_report','_gmail_create_prepared_draft'}
assert [ast.dump(n) for n in tree.body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-recoverable-candidate-20261002');root.mkdir(mode=0o700,exist_ok=True)
p=root/'agent_harness.candidate.private.py';p.write_text(candidate);p.chmod(0o600)
for name in ['email_action_intent.py','gmail_draft_recovery.py']:shutil.copyfile(Path('/tmp')/name,root/name);(root/name).chmod(0o600)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file() and p.name!='manifest.json'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
