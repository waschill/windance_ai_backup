"""Compose outcome reporting and durable autonomy intents in private source."""
import ast,hashlib,json,shutil
from pathlib import Path
from email_action_intent import SCHEMA
base=Path('/Users/herald/backups/email-outcome-candidate-20261002/agent_harness.candidate.private.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='a2f05cc63f743804484d798c37eb9d88478b693895f2b6ded17a8888eb00f640'
s=base.read_text();tree=ast.parse(s);candidate=s
for node in tree.body:
 if getattr(node,'name','')=='db':
  old=ast.get_source_segment(s,node);anchor='        CREATE TABLE IF NOT EXISTS email_autonomy_actions ('
  assert old.count(anchor)==1;candidate=candidate.replace(old,old.replace(anchor,SCHEMA+'\n'+anchor))
 elif getattr(node,'name','')=='gmail_autonomy_report':
  old=ast.get_source_segment(s,node);new=old
  a='                trashed = gmail_delete_message(str(item["id"]))'
  b='                from email_action_intent import perform as mailbox_once\n                trashed = mailbox_once(db, "william", str(item["id"]), "trash", {}, lambda: gmail_delete_message(str(item["id"])))'
  assert new.count(a)==1;new=new.replace(a,b)
  a='                    created = gmail_create_draft(address, f"Re: {item.get(\'subject\') or \'(no subject)\'}", body, item.get("thread_id"))'
  b='                    from email_action_intent import perform as mailbox_once\n                    draft_subject = f"Re: {item.get(\'subject\') or \'(no subject)\'}"\n                    created = mailbox_once(db, "william", str(item["id"]), "draft", {"to": address, "subject": draft_subject, "body": body, "thread_id": item.get("thread_id")}, lambda: gmail_create_draft(address, draft_subject, body, item.get("thread_id")))'
  assert new.count(a)==1;new=new.replace(a,b);candidate=candidate.replace(old,new)
excluded={'db','gmail_autonomy_report'}
assert [ast.dump(n) for n in tree.body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-intent-candidate-20261002');root.mkdir(mode=0o700,exist_ok=True)
target=root/'agent_harness.candidate.private.py';target.write_text(candidate);target.chmod(0o600)
shutil.copyfile('/tmp/email_action_intent.py',root/'email_action_intent.py');(root/'email_action_intent.py').chmod(0o600)
print(json.dumps({'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'journal_sha256':hashlib.sha256((root/'email_action_intent.py').read_bytes()).hexdigest(),'production_changes':False}))
