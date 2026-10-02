import hashlib,json,os,plistlib,re,subprocess
from pathlib import Path
home=Path.home();records=[]
for p in (home/'Library/LaunchAgents').glob('*.plist'):
 try:d=plistlib.loads(p.read_bytes())
 except Exception:continue
 args=d.get('ProgramArguments',[])
 if not any('imessage_outbox_daemon.py' in str(a) for a in args):continue
 label=d['Label'];states=[]
 for domain in ('user','gui'):
  r=subprocess.run(['launchctl','print',f'{domain}/{os.getuid()}/{label}'],capture_output=True,text=True)
  if r.returncode==0:
   m=re.search(r'(?m)^\s*state = (.*)$',r.stdout);pid=re.search(r'(?m)^\s*pid = (\d+)',r.stdout)
   states.append({'domain':domain,'state':m.group(1) if m else 'registered','pid':int(pid.group(1)) if pid else None})
 records.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'label':label,'program':d.get('Program'),
 'program_arguments':args,'keep_alive':d.get('KeepAlive'),'run_at_load':d.get('RunAtLoad'),'working_directory':d.get('WorkingDirectory'),'stdout_path':d.get('StandardOutPath'),'stderr_path':d.get('StandardErrorPath'),'states':states,'environment_keys':sorted(d.get('EnvironmentVariables',{}))})
root=home/'.local/share/windance-imessage-outbox'
ward=home/'services/windance-supervisor'
print(json.dumps({'outbox_services':records,'queue_counts':{n:len(list((root/n).glob('*.json'))) for n in ('queue','inflight','uncertain','claims','results')},'receipt_journal_exists':(root/'journal.db').exists(),'new_runtime_exists':(home/'services/receipt-outbox').exists(),'warden_paused':(ward/'PAUSED').exists(),'warden_jobs_loaded':{l:subprocess.run(['launchctl','print',f'gui/{os.getuid()}/'+l],capture_output=True).returncode==0 for l in ('com.windance.supervisor','com.windance.supervisor-review')}}))
