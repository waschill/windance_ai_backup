"""Guarded privacy repair. No real mail action, dispatch or test notification."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request

ROOT=Path('/Users/herald/backups/email-owner-boundary-20261001T2330Z')
SERVICE=Path('/Users/herald/services/agent-harness')
CANDIDATE=Path('/Users/herald/services/email-owner-boundary-20261001')
DB=Path('/Users/herald/.local/share/agent-harness/harness.db')
OLD='709118f2ae2bf9df5d429e1343c06d709707f8f422db54058085801fca0e3aa7'
NEW='db8a435907a2fb49796818a17b29334874b1919d6a03640901a22b6b12ea8195'
HELPER='02442671b64a239b7b5bbfacdb695fb04c1202bee054ab9543b65a4fecf11f92'
TABLES=['staff_tasks','staff_task_runs','staff_task_deliveries','staff_task_revisions','email_report_active','max_email_report_refs','email_autonomy_actions','approvals']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ro(p):return sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
def hashes(c):return {t:hashlib.sha256(json.dumps(c.execute('select * from '+t+' order by rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in TABLES}
def preflight():
 assert sha(SERVICE/'agent_harness.py')==OLD
 assert sha(CANDIDATE/'agent_harness.py')==NEW and sha(CANDIDATE/'email_owner_boundary.py')==HELPER
 assert not (SERVICE/'email_owner_boundary.py').exists()
 with urllib.request.urlopen('http://127.0.0.1:8793/health',timeout=5) as r:b=json.load(r)
 assert b['active']==0 and b['queued']==0
 c=ro(Path('/Users/herald/.local/share/vega-manager/manager.db'))
 assert c.execute("select count(*) from messages where status in ('queued','submitted')").fetchone()[0]==0
 assert c.execute("select count(*) from projects where status in ('active','review','delivery')").fetchone()[0]==0;c.close()
 c=ro(DB);assert c.execute("select count(*) from staff_tasks where status in ('pending','running','dispatching')").fetchone()[0]==0
 result=hashes(c);c.close();return result
before=preflight()
if sys.argv[1]=='backup':
 ROOT.mkdir(mode=0o700,parents=True,exist_ok=False)
 shutil.copy2(SERVICE/'agent_harness.py',ROOT/'agent_harness.py');(ROOT/'agent_harness.py').chmod(0o600)
 c=ro(DB);b=sqlite3.connect(str(ROOT/'harness.db'));c.backup(b);c.close();assert b.execute('pragma integrity_check').fetchone()[0]=='ok';assert hashes(b)==before;b.close();(ROOT/'harness.db').chmod(0o600)
 shutil.copy2(ROOT/'harness.db',ROOT/'isolated.db');assert sha(ROOT/'harness.db')==sha(ROOT/'isolated.db')
 c=sqlite3.connect('file:'+str(ROOT/'isolated.db')+'?immutable=1',uri=True);assert c.execute('pragma integrity_check').fetchone()[0]=='ok';assert hashes(c)==before;c.close()
 receipt={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'backup_path':str(ROOT),'files':{p.name:sha(p) for p in ROOT.iterdir() if p.is_file()},'table_hashes':before,'cold_restore_verified':True,'production_modified':False}
 (ROOT/'backup-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
elif sys.argv[1]=='deploy':
 receipt=json.loads((ROOT/'backup-receipt.json').read_text());assert before==receipt['table_hashes']
 for name,h in receipt['files'].items():assert sha(ROOT/name)==h
 for name in ['email_owner_boundary.py','agent_harness.py']:
  target=SERVICE/name;temp=SERVICE/(name+'.owner-boundary-tmp');assert not temp.exists()
  temp.write_bytes((CANDIDATE/name).read_bytes());temp.chmod(0o600);os.replace(temp,target)
 subprocess.run(['launchctl','kickstart','-k','user/501/com.windance.agent-harness'],check=True,capture_output=True)
 healthy=False
 for _ in range(30):
  try:
   with urllib.request.urlopen('http://127.0.0.1:8791/health',timeout=2) as r:
    if r.status==200:healthy=True;break
  except Exception:pass
  time.sleep(1)
 assert healthy,'Guarded source installed but health failed; do not auto-restore vulnerable code'
 payload={'user':'Shawn','channel':'vega-internal','message':'delete 99','request_id':'OWNER-BOUNDARY-NOSEND-20261001-valid-grammar'}
 req=urllib.request.Request('http://127.0.0.1:8791/message',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=10) as r:result=json.load(r)
 assert result.get('model')=='mailbox-owner-denied','Live boundary did not withhold'
 c=ro(DB);assert hashes(c)==before,'Protected records changed; reconcile before any replay';c.close()
 out={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'harness_sha256':sha(SERVICE/'agent_harness.py'),'helper_sha256':sha(SERVICE/'email_owner_boundary.py'),'health_http':200,'live_cross_owner_request_withheld':True,'protected_tables_unchanged':True,'real_mailbox_actions':0,'test_sends':0,'backup_path':str(ROOT)}
 (ROOT/'deployment-receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
else:raise ValueError('Unknown mode')
