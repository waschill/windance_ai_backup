"""Compose undo journal, shared recovery holds and primitive receipts."""
import ast,hashlib,json,shutil
from pathlib import Path
from email_undo_intent import SCHEMA
base=Path('/Users/herald/backups/email-shared-harness-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='1006b127bdc08ca8ec5152a9907f3aea5bfb3d6412d767e640999ea19c8dd5f7'
s=p.read_text();candidate=s
for n in ast.parse(s).body:
 name=getattr(n,'name','')
 if name not in {'db','undo_email_autonomy_action','gmail_unarchive','gmail_untrash_to_inbox','gmail_delete_draft'}:continue
 old=ast.get_source_segment(s,n);new=old
 if name=='db':
  a='CREATE INDEX IF NOT EXISTS email_action_intents_state ON email_action_intents(state);';assert new.count(a)==1;new=new.replace(a,a+'\n'+SCHEMA)
 elif name=='undo_email_autonomy_action':
  a='    match = re.match(';assert new.count(a)==1;new=new.replace(a,'    require_william_mailbox()\n'+a)
  start=new.index('    if row["action"] == "archived":');end=new.index('    audit("gmail_autonomy_undo"',start)
  new=new[:start]+'''    from email_undo_intent import perform as perform_undo, UndoHeld
    from email_mailbox_admission import MailboxHeld
    def execute_reversal(saved):
        if saved["action"] == "archived":
            return gmail_unarchive(saved["message_id"])
        if saved["action"] == "trashed":
            return gmail_untrash_to_inbox(saved["message_id"])
        return gmail_delete_draft(saved["draft_id"])
    try:
        receipt = perform_undo(db, int(row["id"]), {"run_id": ref["report_key"], "ordinal": ordinal, "message_id": ref["message_id"]}, execute_reversal, now)
    except (UndoHeld, MailboxHeld):
        return "Email reversal is held for verification. A previous change may already have occurred; do not repeat it until reconciled.", "deterministic", "gmail-autonomy-undo-held"
    result = receipt["reversal_result"]
''' +new[end:]
 elif name=='gmail_delete_draft':
  a='    gmail_service().users().drafts().delete(userId="me", id=draft_id).execute()'
  b='    result = gmail_service().users().drafts().delete(userId="me", id=draft_id).execute(num_retries=0)\n    if result != {}:\n        raise RuntimeError("Unconfirmed draft deletion receipt")'
  assert new.count(a)==1;new=new.replace(a,b)
 else:
  new=new.replace('.execute()','.execute(num_retries=0)')
  if name=='gmail_untrash_to_inbox':
   a='    result = service.users().messages().untrash(userId="me", id=message_id).execute(num_retries=0)'
   b=a+'\n    if not isinstance(result, dict) or result.get("id") != message_id or not isinstance(result.get("labelIds"), list) or "TRASH" in result["labelIds"]:\n        raise RuntimeError("Unconfirmed untrash receipt")'
   assert new.count(a)==1;new=new.replace(a,b)
  pos=new.index('    audit(')
  new=new[:pos]+'''    if not isinstance(result, dict) or result.get("id") != message_id or not isinstance(result.get("labelIds"), list) or "INBOX" not in result["labelIds"] or "TRASH" in result["labelIds"]:
        raise RuntimeError("Unconfirmed Inbox restoration receipt")
'''+new[pos:]
 candidate=candidate.replace(old,new)
excluded={'db','undo_email_autonomy_action','gmail_unarchive','gmail_untrash_to_inbox','gmail_delete_draft'}
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-undo-harness-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for f in base.iterdir():
 if f.suffix=='.py' and f.name!=p.name:
  src=Path('/tmp')/f.name if f.name=='email_mailbox_admission.py' else f
  shutil.copyfile(src,root/f.name);(root/f.name).chmod(0o600)
shutil.copyfile('/tmp/email_undo_intent.py',root/'email_undo_intent.py');(root/'email_undo_intent.py').chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
