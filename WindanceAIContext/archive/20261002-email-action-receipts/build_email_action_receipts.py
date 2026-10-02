"""Compose provider acknowledgment checks into existing Gmail primitives."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/herald/backups/email-selection-harness-20261002');p=base/'agent_harness.candidate.private.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='c4b45ee3cefa7b28667b9316854a3d5400b886a9479333bded6a34d62c78b9d0'
s=p.read_text();candidate=s
spec={'gmail_mark_read':('mark_read','result','message_id'),'gmail_archive':('archive','result','message_id'),'gmail_create_draft':('create_draft','draft','None'),'gmail_send_message':('send','sent','None'),'gmail_send_draft':('send','sent','None')}
for n in ast.parse(s).body:
 if getattr(n,'name','') in spec:
  kind,var,expected=spec[n.name];old=ast.get_source_segment(s,n);new=old
  assert new.count('.execute()')==1;new=new.replace('.execute()','.execute(num_retries=0)')
  pos=new.index('    audit(');new=new[:pos]+f'    from gmail_action_receipts import validate_ack\n    validate_ack("{kind}", {var}, {expected})\n'+new[pos:]
  candidate=candidate.replace(old,new)
assert [ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in spec]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in spec]
root=Path('/Users/herald/backups/email-action-receipts-20261002');root.mkdir(mode=0o700,exist_ok=False)
(root/p.name).write_text(candidate);(root/p.name).chmod(0o600)
for f in base.iterdir():
 if f.suffix=='.py' and f.name!=p.name:shutil.copyfile(f,root/f.name);(root/f.name).chmod(0o600)
shutil.copyfile('/tmp/gmail_action_receipts.py',root/'gmail_action_receipts.py');(root/'gmail_action_receipts.py').chmod(0o600)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()};(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'candidate_files_sha256':manifest,'production_changes':False}))
