"""Owner-approved unchanged launch registration; no work replay."""
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import time
import urllib.request

h=Path.home();label='com.windance.agent-harness';domain='user/501'
plist=h/'Library/LaunchAgents'/ (label+'.plist')
source=h/'services/agent-harness/agent_harness.py'
assert hashlib.sha256(plist.read_bytes()).hexdigest()=='5e7597948183dc177137902369f6c234968a02da5f3ced8e9a555be315a46e2c'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='709118f2ae2bf9df5d429e1343c06d709707f8f422db54058085801fca0e3aa7'
for d in ['user/501','gui/501']:
    assert subprocess.run(['/bin/launchctl','print',d+'/'+label],capture_output=True).returncode!=0,'Already registered; do not duplicate'
def ledger():
    c=sqlite3.connect('file:'+str(h/'.local/share/agent-harness/harness.db')+'?mode=ro',uri=True)
    c.execute('pragma query_only=ON');c.execute('begin')
    out={}
    for table in ['staff_tasks','staff_task_deliveries','staff_task_runs','staff_task_revisions']:
        rows=c.execute('select * from '+table+' order by rowid').fetchall()
        out[table]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,default=str).encode()).hexdigest()}
    states=dict(c.execute('select status,count(*) from staff_tasks group by status'))
    c.close();return out,states
before,states=ledger()
assert not any(states.get(s,0) for s in ['running','pending','queued','dispatching']),'Active work requires reconciliation'
record=h/'backups/agentic-baseline-20261001T0447Z'
(record/'registration-preflight.json').write_text(json.dumps({'task_state':before,'status_counts':states},indent=2)+'\n')
result=subprocess.run(['/bin/launchctl','bootstrap',domain,str(plist)],capture_output=True,text=True)
if result.returncode!=0:
    print(json.dumps({'status':'registration_failed','returncode':result.returncode,'error':result.stderr.strip()[:300]}))
    raise SystemExit(1)
health=None
for _ in range(24):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8791/health',timeout=2) as r:
            if r.status==200:health=json.load(r);break
    except Exception:pass
    time.sleep(1)
after,after_states=ledger()
healthy=bool(health and health.get('status') in ('ok','healthy'))
unchanged=before==after and states==after_states
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'domain':domain,'label':label,
         'health_http':200 if health else None,'health_status':health.get('status') if health else None,
         'health_keys':sorted(health) if health else [],'operational_ledger_unchanged':unchanged,
         'status_counts':after_states,'explicit_task_dispatches':0,'rollback_performed':False}
if not healthy or not unchanged:
    rollback=subprocess.run(['/bin/launchctl','bootout',domain+'/'+label],capture_output=True)
    receipt['rollback_performed']=rollback.returncode==0
    receipt['status']='verification_failed'
else:receipt['status']='recovered'
(record/'registration-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
if receipt['status']!='recovered':raise SystemExit(1)
