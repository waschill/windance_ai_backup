"""Stage atomic whole-Gmail-approval claim; selected-number path remains separate."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-trash-receipt-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='1e011c5263479660998b817fb423e34408ce0426a0f8e6279cf0d70cd4d85e4b'
s=p.read_text();node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='approve_pending');old=ast.get_source_segment(s,node);new=old
a='    payload = json.loads(approval["payload_json"])'
b=a+'''
    gmail_claim = str(approval["action"]).startswith("gmail.")
    if gmail_claim:
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            changed = conn.execute(
                "UPDATE approvals SET status='executing', decision_note='Execution claimed; result not yet confirmed' WHERE id=? AND status='pending' AND action=? AND payload_json=? AND requested_at=?",
                (approval["id"], approval["action"], approval["payload_json"], approval["requested_at"]),
            ).rowcount
            conn.commit()
        if changed != 1:
            return "This approval changed or is already being handled. No action was repeated; review its existing status.", "deterministic", "approval-held"
'''
assert new.count(a)==1;new=new.replace(a,b)
a='        status = "failed"'
b='        status = "uncertain" if gmail_claim else "failed"'
assert new.count(a)==1;new=new.replace(a,b)
a='        response = f"I approved it, but execution failed for {approval[\'action\']} ({approval[\'id\'][:8]}): {str(exc)[:500]}"'
b=a+'''
        if gmail_claim:
            result = {"error": "execution_outcome_unconfirmed"}
            response = "Approval was accepted, but its mailbox outcome is unconfirmed. Do not repeat it until reconciled."
'''
assert new.count(a)==1;new=new.replace(a,b)
a='"UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=?",\n            (status, now(), note or json.dumps(result, default=str)[:1000], approval["id"]),'
b='"UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=? AND status=?",\n            (status, now(), note or json.dumps(result, default=str)[:1000], approval["id"], "executing" if gmail_claim else "pending"),'
assert new.count(a)==1;new=new.replace(a,b)
candidate=s.replace(old,new)
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','')!='approve_pending']==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','')!='approve_pending']
root=Path('/Users/herald/backups/email-approval-claim-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for name in ['email_action_intent.py','gmail_draft_recovery.py']:shutil.copyfile(base/name,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
