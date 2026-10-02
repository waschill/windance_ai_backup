"""Read-only saved Windance definitions versus own-user launch registrations."""
import datetime,hashlib,json,os,plistlib,subprocess
from pathlib import Path
root=Path.home()/'Library/LaunchAgents';uid=os.getuid();rows=[]
for p in sorted(root.glob('*.plist')):
    if not any(s in p.name.lower() for s in ('windance','herald','reacher','vega','warden','profile-staff')):continue
    raw=p.read_bytes()
    try:d=plistlib.loads(raw)
    except Exception as exc:
        rows.append({'file':p.name,'parse_error':type(exc).__name__});continue
    label=d.get('Label')
    if not isinstance(label,str) or '/' in label:continue
    registrations={}
    for domain in (f'user/{uid}',f'gui/{uid}'):
        try:
            r=subprocess.run(['launchctl','print',domain+'/'+label],capture_output=True,text=True,timeout=3)
            registrations[domain]={'registered':r.returncode==0,'state':[s.strip() for s in r.stdout.splitlines() if s.strip().startswith(('state =','last exit code =','runs ='))]}
        except subprocess.TimeoutExpired:registrations[domain]={'unverified':'timeout'}
    rows.append({'file':p.name,'label':label,'sha256':hashlib.sha256(raw).hexdigest(),
                 'run_at_load':d.get('RunAtLoad') is True,'disabled_in_definition':d.get('Disabled') is True,
                 'start_interval':d.get('StartInterval'),'calendar_schedule_present':'StartCalendarInterval' in d,
                 'registrations':registrations})
print(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Selected own-user LaunchAgents only; no system domains, cron, Node-RED or launch-state mutation',
 'definitions':rows,'production_changes':False}))
