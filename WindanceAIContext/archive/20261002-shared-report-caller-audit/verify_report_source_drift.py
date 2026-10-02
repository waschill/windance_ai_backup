import hashlib,json,plistlib,subprocess,urllib.request
from pathlib import Path
out={}
for name,path in {'harness':'/Users/herald/services/agent-harness/agent_harness.py','execution_bridge':'/Users/herald/services/windance-codex-bridge/server.mjs','notification_bridge':'/Users/herald/services/vega-task-bridge/vega_task_bridge.py'}.items():
 p=Path(path);out[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'modified_unix':p.stat().st_mtime}
 if name=='harness':out[name]['early_rejection_marker_present']='secret_like_memory_content' in p.read_text()
plists=[]
for p in (Path.home()/'Library/LaunchAgents').glob('*.plist'):
 try:d=plistlib.loads(p.read_bytes())
 except Exception:continue
 args=d.get('ProgramArguments',[])
 if not any(isinstance(a,str) and ('agent_harness.py' in a or 'vega_task_bridge.py' in a) for a in args):continue
 label=d.get('Label');states=[]
 for domain in ('user/501/','gui/501/'):
  r=subprocess.run(['launchctl','print',domain+label],capture_output=True)
  if r.returncode==0:states.append(domain)
 plists.append({'label':label,'script_paths':[a for a in args if a.endswith('.py')],'registered_domains':states})
out['service_paths']=plists
try:
 with urllib.request.urlopen('http://127.0.0.1:8791/health',timeout=3) as r:out['harness_health_http']=r.status
except Exception as e:out['health_failure_type']=type(e).__name__
print(json.dumps(out))
