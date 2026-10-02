"""Stage exact receipt validation without changing mailbox action authority."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-rule-intent-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='d86047aa69dd5a5703794a3143dfeba24cee66a072a81f210d321bb8ed7915fc'
s=p.read_text();node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='gmail_delete_message');old=ast.get_source_segment(s,node)
new='''def gmail_delete_message(message_id: str) -> dict[str, Any]:
    """Move to Trash after confirmed mark-read; never permanently delete."""
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("Message identity required")
    service = gmail_service()
    try:
        marked = service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute(num_retries=0)
        if not isinstance(marked, dict) or marked.get("id") != message_id or not isinstance(marked.get("labelIds"), list) or "UNREAD" in marked["labelIds"]:
            raise RuntimeError("Unconfirmed mark-read receipt")
        result = service.users().messages().trash(userId="me", id=message_id).execute(num_retries=0)
        if not isinstance(result, dict) or result.get("id") != message_id or not isinstance(result.get("labelIds"), list) or "TRASH" not in result["labelIds"]:
            raise RuntimeError("Unconfirmed Trash receipt")
    except Exception:
        audit("gmail_trash_outcome_unconfirmed", {"reason": "missing_or_failed_receipt"})
        raise RuntimeError("Mailbox change outcome unconfirmed; reconcile before retrying") from None
    audit("gmail_trashed", {"message_id": message_id, "marked_read": True})
    return {"trashed": True, "marked_read": True, "id": message_id}
'''
candidate=s.replace(old,new)
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','')!='gmail_delete_message']==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','')!='gmail_delete_message']
root=Path('/Users/herald/backups/email-trash-receipt-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for name in ['email_action_intent.py','gmail_draft_recovery.py']:shutil.copyfile(base/name,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
