"""Compose shared mailbox admission and deterministic report hold notice."""
import ast,hashlib,json,shutil
from pathlib import Path
from email_mailbox_admission import SCHEMA
base=Path('/Users/herald/backups/email-single-intent-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='709770df371403ec2ce31d38246754d54cc2cce1d0793e423aeae7bd3a4ba33b'
s=p.read_text();candidate=s
for n in ast.parse(s).body:
 if getattr(n,'name','')=='db':
  old=ast.get_source_segment(s,n);a='CREATE INDEX IF NOT EXISTS email_action_intents_state ON email_action_intents(state);';assert old.count(a)==1;candidate=candidate.replace(old,old.replace(a,a+'\n'+SCHEMA))
 elif getattr(n,'name','')=='gmail_autonomy_report':
  old=ast.get_source_segment(s,n);new=old
  a='    from email_action_intent import report_state, operation_key'
  b=a+'''
    from email_mailbox_admission import is_held
    if is_held(db):
        return "Email authority report\\n\\nAn earlier mailbox action is active or unconfirmed. Automatic changes are held pending verification. This report started no new classification or mailbox action.", "deterministic", "gmail-autonomy-held"
'''
  assert new.count(a)==1;new=new.replace(a,b)
  a='    items, explicit_rule_notices = apply_email_sender_rules(items)'
  b=a+'''
    if is_held(db):
        return "Email authority report\\n\\nA sender-rule outcome requires verification. Further automatic changes are held. Earlier attempted changes may already have occurred.", "deterministic", "gmail-autonomy-held"
'''
  assert new.count(a)==1;new=new.replace(a,b);candidate=candidate.replace(old,new)
excluded={'db','gmail_autonomy_report'}
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in excluded]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in excluded]
root=Path('/Users/herald/backups/email-shared-harness-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
replaced={'email_action_intent.py','email_approved_item_intent.py'}
for f in base.iterdir():
 if f.suffix=='.py' and f.name!=p.name:
  src=Path('/tmp')/f.name if f.name in replaced else f
  shutil.copyfile(src,root/f.name);(root/f.name).chmod(0o600)
shutil.copyfile('/tmp/email_mailbox_admission.py',root/'email_mailbox_admission.py');(root/'email_mailbox_admission.py').chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
