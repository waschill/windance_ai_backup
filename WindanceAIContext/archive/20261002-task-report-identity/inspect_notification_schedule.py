import json,plistlib,subprocess,os
from pathlib import Path
records=[]
for p in (Path.home()/'Library/LaunchAgents').glob('*.plist'):
 try:d=plistlib.loads(p.read_bytes())
 except Exception:continue
 label=d.get('Label','');args=d.get('ProgramArguments',[])
 if 'vega-task' not in label and not any('vega_task_bridge' in str(a) for a in args):continue
 states=[]
 for domain in ('user','gui'):
  r=subprocess.run(['launchctl','print',f'{domain}/{os.getuid()}/{label}'],capture_output=True)
  if r.returncode==0:states.append(domain)
 records.append({'label':label,'registered':states,'interval':d.get('StartInterval'),'run_at_load':d.get('RunAtLoad',False)})
r=subprocess.run(['crontab','-l'],capture_output=True,text=True)
print(json.dumps({'matching_launch_agents':records,'crontab_read_exit':r.returncode,'crontab_bridge_reference':('vega_task_bridge' in r.stdout or 'vega-task-bridge' in r.stdout),'scope':'current user launch plists and crontab only'}))
