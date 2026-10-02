"""Installed metadata and no-admission query check; no message body inspection."""
import hashlib,json,os,re,subprocess,time
from pathlib import Path
home=Path.home();root=home/'.local/share/windance-imessage-outbox';runtime=home/'services/receipt-outbox'
manifest=json.loads((runtime/'runtime-manifest.json').read_text())
assert all(hashlib.sha256((runtime/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
job=subprocess.run(['launchctl','print','gui/501/com.windance.imessage-outbox'],capture_output=True,text=True,check=True)
pid=int(re.search(r'(?m)^\s*pid = (\d+)',job.stdout).group(1))
status=json.loads((root/'dispatcher-status.json').read_text())
assert status['pid']==pid and status['state']=='idle' and time.time()-status['observed_unix']<40
def state():return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('queue','claims','results','inflight','uncertain') for p in (root/folder).glob('*.json')}
before=state()
request={'key':'synthetic-read-only-installed-query-20261002','payload':{'to':'synthetic-no-send','chunks':['synthetic query only'],'sms':False}}
python='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python'
start=time.monotonic()
r=subprocess.run([python,'-B',str(runtime/'outbox_protocol_cli.py'),'--root',str(root),'--mode','query','--wait-seconds','.5'],input=json.dumps(request),capture_output=True,text=True,timeout=3)
elapsed=round(time.monotonic()-start,3)
assert r.returncode==14 and json.loads(r.stdout)['result']['status']=='unknown'
assert state()==before
assert (home/'services/windance-supervisor/PAUSED').exists()
assert all(subprocess.run(['launchctl','print','gui/501/'+n],capture_output=True).returncode!=0 for n in ('com.windance.supervisor','com.windance.supervisor-review'))
print(json.dumps({'installed_runtime_hashes_verified':len(manifest),'pid':pid,'idle_status_fresh':True,
                  'installed_readonly_query_passed':True,'query_seconds':elapsed,'delivery_state_unchanged':True,
                  'warden_pause_preserved':True,'manual_sends':0,'admissions':0}))
