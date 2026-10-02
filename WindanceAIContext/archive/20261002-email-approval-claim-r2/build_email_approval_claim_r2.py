"""Tighten atomic claim freshness and final receipt acknowledgment."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-approval-claim-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='60b315cb16b43a8f310bf0db21f057f0d450056aa3c74bd81a89adb8423a8e69'
s=p.read_text();node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='approve_pending');old=ast.get_source_segment(s,node);new=old
a='            conn.execute("BEGIN IMMEDIATE")'
b=a+'''
            if not approval_is_fresh(approval):
                conn.rollback()
                return "Approval expired before execution could be claimed. No action was started.", "deterministic", "approval-expired"
'''
assert new.count(a)==1;new=new.replace(a,b)
a='''        conn.execute(
            "UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=? AND status=?",'''
b='''        final_receipt = conn.execute(
            "UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=? AND status=?",'''
assert new.count(a)==1;new=new.replace(a,b)
a='''        conn.commit()
    audit("approval_decided",'''
b='''        if final_receipt.rowcount != 1:
            conn.rollback()
            raise RuntimeError("Approval outcome could not be recorded because its status changed; reconcile before retrying")
        conn.commit()
    audit("approval_decided",'''
assert new.count(a)==1;new=new.replace(a,b)
candidate=s.replace(old,new)
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','')!='approve_pending']==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','')!='approve_pending']
root=Path('/Users/herald/backups/email-approval-claim-r2-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for name in ['email_action_intent.py','gmail_draft_recovery.py']:shutil.copyfile(base/name,root/name);(root/name).chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
