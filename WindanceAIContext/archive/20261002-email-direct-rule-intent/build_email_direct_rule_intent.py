"""Journal the remaining immediate numbered sender-rule Trash calls."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-undo-harness-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='6f4966471558b352183115f7b7c276309e9aee5a1fed7cb642883ba992a0ba87'
s=p.read_text();node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='prepare_gmail_report_reply_actions');old=ast.get_source_segment(s,node);new=old
a='    text = re.sub(';pos=new.index(a);new=new[:pos]+'    require_william_mailbox()\n'+new[pos:]
a='    lines: list[str] = []';b='''    from email_mailbox_admission import is_held
    if is_held(db):
        return "An earlier mailbox action is active or unconfirmed. This command made no new rule or mailbox change; reconcile the earlier action first.", "deterministic", "gmail-summary-held"
    from email_action_intent import perform as mailbox_once
'''+a
assert new.count(a)==1;new=new.replace(a,b)
for rule in ['always_delete','notify_delete']:
 a=f'            address = upsert_email_sender_rule("{rule}", ref)\n            gmail_delete_message(ref["message_id"])'
 b=f'''            address = upsert_email_sender_rule("{rule}", ref)
            scope = "sender-rule:{rule}:" + str(ref["report_key"]) + ":" + str(ref_num)
            mailbox_once(db, "william", str(ref["message_id"]), "trash", {{}}, lambda: gmail_delete_message(ref["message_id"]), operation_scope=scope)'''
 assert new.count(a)==1;new=new.replace(a,b)
for label in ['always delete','notify delete']:
 a=f'            lines.append(f"- {label} failed for {{label}}: {{str(exc)[:180]}}")'
 b=f'            lines.append(f"- {label} requires verification for {{label}}. The sender rule may have been saved and the mailbox change may have occurred; do not repeat blindly.")'
 assert new.count(a)==1;new=new.replace(a,b)
candidate=s.replace(old,new)
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','')!='prepare_gmail_report_reply_actions']==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','')!='prepare_gmail_report_reply_actions']
root=Path('/Users/herald/backups/email-direct-rule-intent-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for f in base.iterdir():
 if f.suffix=='.py' and f.name!=p.name:
  src=Path('/tmp/email_action_intent.py') if f.name=='email_action_intent.py' else f
  shutil.copyfile(src,root/f.name);(root/f.name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
