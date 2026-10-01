"""Inspect/cold-test before restoring the unchanged registered-work monitor."""
from __future__ import annotations
import ast
import contextlib
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

ROOT=Path('/Users/herald/backups/staff-monitor-recovery-20261001T2310Z')
DB=Path('/Users/herald/.local/share/agent-harness/harness.db')
SOURCE=Path('/Users/herald/services/agent-harness/dispatch_health.py')
MONITOR=Path('/Users/herald/services/profile-staff-runner/staff_follow_through_monitor.py')
PLIST=Path('/Users/herald/Library/LaunchAgents/com.windance.profile-staff-runner.plist')
LABEL='com.windance.profile-staff-runner'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dbread(path=DB):return sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
def checks(c):
 assert c.execute("select count(*) from staff_task_runs r join staff_tasks t on t.id=r.task_id where t.status in ('pending','running','dispatching')").fetchone()[0]==0
 assert c.execute("select count(*) from staff_task_runs r join staff_tasks t on t.id=r.task_id join staff_task_deliveries d on d.task_id=r.task_id where t.status in ('completed','partial','failed','blocked') and r.delivery_retries<3 and d.status='failed'").fetchone()[0]==0
 return {t:hashlib.sha256(json.dumps(c.execute('select * from '+t+' order by rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in ['staff_tasks','staff_task_runs','staff_task_deliveries','staff_task_revisions']}
for domain in ['user/501','gui/501']:
 assert subprocess.run(['launchctl','print',domain+'/'+LABEL],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
c=dbread();before=checks(c)
if sys.argv[1]=='backup':
 ROOT.mkdir(mode=0o700,parents=True,exist_ok=False)
 b=sqlite3.connect(str(ROOT/'harness.db'));c.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok';assert checks(b)==before;b.close();c.close();(ROOT/'harness.db').chmod(0o600)
 for p in [SOURCE,MONITOR,PLIST]:shutil.copy2(p,ROOT/p.name);(ROOT/p.name).chmod(0o600);assert sha(p)==sha(ROOT/p.name)
 cold=ROOT/'isolated.db';shutil.copy2(ROOT/'harness.db',cold);assert sha(cold)==sha(ROOT/'harness.db')
 @contextlib.contextmanager
 def isolated_db():
  connection=sqlite3.connect(str(cold));connection.row_factory=sqlite3.Row
  try:yield connection
  finally:connection.close()
 def forbidden(*a,**k):raise AssertionError('Unexpected side effect')
 tree=ast.parse(SOURCE.read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['age_seconds','init','follow_through']]
 ns={'dt':dt,'os':os,'redispatch_pending':forbidden};exec(compile(ast.Module(body=functions,type_ignores=[]),'<isolated-monitor>','exec'),ns)
 result=ns['follow_through']({'db':isolated_db,'audit':forbidden,'complete_staff_task':forbidden,'find_staff_task':forbidden,'deliver_staff_task_result':forbidden})
 assert result=={'ok':True,'followups':0,'invalid_timestamps':0,'legacy_queue_swept':False}
 c=dbread(cold);assert checks(c)==before;c.close()
 receipt={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'backup_path':str(ROOT),'files':{p.name:sha(p) for p in ROOT.iterdir() if p.is_file()},'ledger_hashes':before,'isolated_result':result,'production_started':False}
 (ROOT/'backup-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
elif sys.argv[1]=='restore':
 c.close();receipt=json.loads((ROOT/'backup-receipt.json').read_text());assert before==receipt['ledger_hashes']
 for p in [SOURCE,MONITOR,PLIST]:assert sha(p)==receipt['files'][p.name]
 for name,h in receipt['files'].items():assert sha(ROOT/name)==h
 log=Path('/Users/herald/logs/profile-staff-runner/out.log');offset=log.stat().st_size if log.exists() else 0
 subprocess.run(['launchctl','bootstrap','user/501',str(PLIST)],capture_output=True,check=True)
 try:
  row=None
  for attempt in range(30):
   if log.exists():
    with log.open('rb') as f:f.seek(offset);lines=f.read().decode('utf-8','replace').splitlines()
    for line in lines:
     try:
      candidate=json.loads(line)
      if candidate.get('ok') is True:row=candidate
     except ValueError:pass
   if row:break
   time.sleep(1)
  assert row and row.get('followups')==0 and row.get('legacy_queue_swept') is False and row.get('invalid_timestamps')==0,'No clean monitor receipt'
  c=dbread();assert checks(c)==before,'Live task/delivery state changed';c.close()
  result={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'loaded':LABEL,'domain':'user/501','monitor_receipt':row,'ledger_unchanged':True,'explicit_sends':0,'replayed_tasks':0,'backup_path':str(ROOT)}
  (ROOT/'restoration-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 except Exception:
  subprocess.run(['launchctl','bootout','user/501/'+LABEL],capture_output=True);raise
else:raise ValueError('Unknown mode')
