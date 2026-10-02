"""Prepare private service candidate only; no registration or runtime creation."""
import hashlib,json,plistlib,subprocess
from pathlib import Path
home=Path.home();original=home/'Library/LaunchAgents/com.windance.imessage-outbox.plist'
assert hashlib.sha256(original.read_bytes()).hexdigest()=='d1f6f9555b68822540ad6eb67531fba100156f21a00131abad0d417083a04692'
stage=home/'backups/receipt-launch-candidate-20261002';stage.mkdir(mode=0o700,exist_ok=False)
before=plistlib.loads(original.read_bytes());after=dict(before)
runtime=home/'services/receipt-outbox';root=home/'.local/share/windance-imessage-outbox'
after['ProgramArguments']=[before['ProgramArguments'][0],'-B',str(runtime/'receipt_outbox_dispatcher.py'),
 '--root',str(root),'--source',str(home/'bin/imessage_outbox_daemon.py'),
 '--database',str(home/'Library/Messages/chat.db'),'--wheel',str(runtime/'pytypedstream-0.1.0-py3-none-any.whl'),
 '--request-seconds','600']
assert {k:v for k,v in before.items() if k!='ProgramArguments'}=={k:v for k,v in after.items() if k!='ProgramArguments'}
(stage/'original.plist').write_bytes(original.read_bytes())
candidate=stage/'candidate.plist';candidate.write_bytes(plistlib.dumps(after));candidate.chmod(0o600)
(stage/'original.plist').chmod(0o600)
r=subprocess.run(['plutil','-lint',str(candidate)],capture_output=True);assert r.returncode==0
assert original.read_bytes()==(stage/'original.plist').read_bytes()
print(json.dumps({'candidate_path':str(candidate),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'only_program_arguments_changed':True,'plist_lint_passed':True,'registered':False}))
