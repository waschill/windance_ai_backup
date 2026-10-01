"""Owner-authorized temporary Warden suspension; keep code and incident state."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

root=Path('/Users/zuzu/services/windance-supervisor')
record=root/'operator-directions/agentic-project-20261001';record.mkdir(parents=True,exist_ok=True)
labels=['com.windance.supervisor-review','com.windance.supervisor']
jobs=[]
for label in labels:
    p=Path.home()/'Library/LaunchAgents'/(label+'.plist')
    assert p.is_file()
    loaded=subprocess.run(['/bin/launchctl','print','gui/501/'+label],capture_output=True).returncode==0
    jobs.append({'label':label,'domain':'gui/501','plist':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'was_loaded':loaded})
assert all(j['was_loaded'] for j in jobs),'Unexpected prior job state; inspect before changing'
(record/'restore-jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
direction='''William explicitly approved the coordinated training correction and loading the unchanged Harness service in this Codex chat. He also authorized removing Warden checks until this project is done. Implement as temporary pause plus unloading the two existing Warden jobs, without changing its code, incidents, review policy or reservations. Restore these exact jobs and resume supervision at project completion after health verification. Training-note collection remains suspended and its rebuild is deferred until after this goal. No permission to re-enable phone, alter SyncThing/Level8 or interrupt protected SAM hours follows.\n'''
(record/'WILLIAM_DIRECTION.md').write_text(direction)
incident=root/'operator-directions/INC-20260930-51ef44e0';incident.mkdir(parents=True,exist_ok=True)
(incident/'WILLIAM_DIRECTION.md').write_text(direction+'Specific Harness operation: load unchanged com.windance.agent-harness into user/501, verify health and unchanged task/delivery state, unload same registration if startup fails. No task replay or model-route change.\n')
pause=subprocess.run(['/usr/bin/python3',str(root/'supervisor.py'),'pause'],capture_output=True,text=True,timeout=70)
assert pause.returncode==0,'Pause did not confirm quiescence; no unload permitted'
assert (root/'PAUSED').exists()
for job in jobs:
    result=subprocess.run(['/bin/launchctl','bootout',job['domain']+'/'+job['label']],capture_output=True)
    assert result.returncode==0,'Job unload failed; inspect preserved job state'
for job in jobs:
    assert subprocess.run(['/bin/launchctl','print',job['domain']+'/'+job['label']],capture_output=True).returncode!=0
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'paused':True,'jobs_unloaded':labels,'record_directory':str(record),'incidents_modified':False,'code_modified':False,'restoration_required_at_project_completion':True}
(record/'suspension-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
