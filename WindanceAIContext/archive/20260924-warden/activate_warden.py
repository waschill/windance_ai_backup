"""Activate only the tested SAL supervisor, preserving other jobs."""
import datetime as dt
import hashlib
import json
import os
import plistlib
import subprocess
from pathlib import Path
EXPECTED_MANIFEST_SHA256 = '0b2441feee9faa3e0e4bc8d96dc1e88605be1ef1b5f974ac6e8a18bc249bbd9e'
if Path.home().name!='zuzu': raise RuntimeError('Activation is SAL only')
root=Path('/Users/zuzu/services/windance-supervisor')
subprocess.run(['/usr/bin/python3',str(root/'supervisor.py'),'pause'],check=True)
manifest=root/'deployment-manifest.json'
if hashlib.sha256(manifest.read_bytes()).hexdigest()!=EXPECTED_MANIFEST_SHA256:
    raise RuntimeError('Deployment manifest differs from the reviewed activation source')
expected=json.loads(manifest.read_text())
required={'supervisor.py','review_gate.py','remote_ops.py','report_wrapper.py','config.json'}
if set(expected)!=required|{'claude_review.py'}: raise RuntimeError('Incomplete deployment manifest')
actual={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in required}
if actual!={k:expected[k] for k in required}: raise RuntimeError('SAL deployment differs from reviewed manifest')
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','HERALD',
    '/Users/herald/.hermes/hermes-agent/venv/bin/python','/Users/herald/services/windance-supervisor/remote_ops.py','fingerprints'],
    capture_output=True,text=True,timeout=30,check=True)
if json.loads(p.stdout)!=expected: raise RuntimeError('Herald deployment differs from reviewed manifest')
plist=Path.home()/'Library/LaunchAgents/com.windance.supervisor.plist'
value=plistlib.loads(plist.read_bytes())
if value.get('Label')!='com.windance.supervisor' or value.get('ProgramArguments')!=['/usr/bin/python3',str(root/'supervisor.py'),'once'] or value.get('StartInterval')!=120:
    raise RuntimeError('Supervisor launch configuration differs from reviewed plan')
value.setdefault('EnvironmentVariables',{})['PATH']='/usr/bin:/bin:/usr/sbin:/sbin:/Applications/ChatGPT.app/Contents/Resources'
plist.write_bytes(plistlib.dumps(value))
review_plist=plist.with_name('com.windance.supervisor-review.plist')
review_value=dict(value)
review_value['Label']='com.windance.supervisor-review'
review_value['ProgramArguments']=['/usr/bin/python3',str(root/'supervisor.py'),'review-once']
review_value['StandardOutPath']=str(Path.home()/'logs/windance-supervisor/review.log')
review_value['StandardErrorPath']=str(Path.home()/'logs/windance-supervisor/review-error.log')
review_plist.write_bytes(plistlib.dumps(review_value))
try:
    for job_path in (plist,review_plist):
        target='gui/'+str(os.getuid())+'/'+job_path.stem
        existing=subprocess.run(['/bin/launchctl','print',target],capture_output=True)
        if not existing.returncode: raise RuntimeError('Job already loaded; use a reviewed maintenance update')
        subprocess.run(['/bin/launchctl','bootstrap','gui/'+str(os.getuid()),str(job_path)],check=True)
    subprocess.run(['/usr/bin/python3',str(root/'supervisor.py'),'resume'],check=True)
    for job_path in (plist,review_plist):
        subprocess.run(['/bin/launchctl','kickstart','gui/'+str(os.getuid())+'/'+job_path.stem],check=True)
except BaseException:
    (root/'PAUSED').write_text(dt.datetime.now(dt.timezone.utc).isoformat())
    raise
record={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'host':'SAL','jobs':['com.windance.supervisor','com.windance.supervisor-review'],'interval_seconds':value['StartInterval'],'enabled':True}
(root/'activation-receipt.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
