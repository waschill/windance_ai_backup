"""Idempotent installation; source files must already be copied and tested."""
import datetime as dt
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
from pathlib import Path

home=Path.home()
root=home/'services/windance-supervisor'
data=home/'.local/share/windance-supervisor'
backup=root/'backups/initial'
backup.mkdir(parents=True,exist_ok=True)
data.mkdir(parents=True,exist_ok=True)
os.chmod(data,0o700)
if not (data/'activation.json').exists():
    (data/'activation.json').write_text(json.dumps({'at':dt.datetime.now(dt.timezone.utc).isoformat()}))
if home.name == 'zuzu':
    report=home/'Library/LaunchAgents/com.windance.youtube-briefing.plist'
    if not (backup/report.name).exists(): shutil.copy2(report,backup/report.name)
    original=plistlib.loads((backup/report.name).read_bytes())
    config={'argv':original['ProgramArguments']}
    if any('--print-only' in arg or '--json' == arg for arg in config['argv']):
        raise RuntimeError('Scheduled command is not a delivery command')
    (data/'report-command.json').write_text(json.dumps(config))
    updated=dict(original)
    updated['ProgramArguments']=['/usr/bin/python3',str(root/'report_wrapper.py')]
    updated['WorkingDirectory']=original.get('WorkingDirectory',str(home/'bin'))
    before=hashlib.sha256(report.read_bytes()).hexdigest()
    # Refuse to overwrite somebody else's concurrent schedule edit.
    current=plistlib.loads(report.read_bytes())
    if current != original and current != updated:
        raise RuntimeError('Report plist changed concurrently')
    report.write_bytes(plistlib.dumps(updated))
    target=f'gui/{os.getuid()}/com.windance.youtube-briefing'
    subprocess.run(['/bin/launchctl','bootout',target],capture_output=True)
    subprocess.run(['/bin/launchctl','bootstrap',f'gui/{os.getuid()}',str(report)],check=True)
    service=home/'Library/LaunchAgents/com.windance.supervisor.plist'
    payload={'Label':'com.windance.supervisor','ProgramArguments':['/usr/bin/python3',str(root/'supervisor.py'),'once'],
        'WorkingDirectory':str(root),'StartInterval':120,'RunAtLoad':True,
        'ProcessType':'Background','StandardOutPath':str(home/'logs/windance-supervisor/run.log'),
        'StandardErrorPath':str(home/'logs/windance-supervisor/error.log'),
        'EnvironmentVariables':{'PATH':'/usr/bin:/bin:/usr/sbin:/sbin:/Applications/ChatGPT.app/Contents/Resources'},
        'AbandonProcessGroup':False}
    service.write_bytes(plistlib.dumps(payload))
    # Launch only after the explicit activate step; initial service is paused.
    print(json.dumps({'installed':True,'report_schedule_preserved':original['StartCalendarInterval']==updated['StartCalendarInterval'],
                      'original_report_sha256':before,'supervisor_loaded':False}))
else:
    print(json.dumps({'installed':True,'host':'HERALD','activation':'recorded'}))
