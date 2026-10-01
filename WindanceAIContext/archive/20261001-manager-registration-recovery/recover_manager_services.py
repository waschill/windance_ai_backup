"""Guarded restoration of unchanged registrations; no task or send invocation."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request

ROOT = Path('/Users/herald/backups/manager-recovery-20261001T2305Z')
DB = Path('/Users/herald/.local/share/vega-manager/manager.db')
STATE = Path('/Users/herald/.local/share/windance-codex/state.json')
HASHES = {
 '/Users/herald/services/vega-manager/manager.py':'1d2c67417ca4080158db8e5c9840b5c602523856bfc7551ad0f2c8276a4c7a83',
 '/Users/herald/services/windance-codex-bridge/server.mjs':'62483284dea6eefe010ea9d34cc4bb4438a6042bb910462f8679ab676ef80c1c',
 '/Users/herald/Library/LaunchAgents/com.windance.vega-manager.plist':'fe4dca3bdffc2448fcd91a21a853a18e12b1311737fbf5aeb53818ce8b506a58',
 '/Users/herald/Library/LaunchAgents/com.windance.codex-bridge.plist':'d3dc628d91d0e9956daef468a2b2b4b790496a8918db584018599cfdf8bc7931',
 '/Users/herald/Library/LaunchAgents/com.windance.codex-app-server.plist':'1fd8d9be39a8c7918798344332177a0a863cf6acc8a84af464642d13b1333d68',
}
LABELS = ['com.windance.codex-app-server','com.windance.codex-bridge','com.windance.vega-manager']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def connect(): return sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True)
def ledger(c):
 return {t:hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in ['projects','stages','events','messages']}
def preflight():
 for p,h in HASHES.items(): assert sha(p)==h, 'Source drift: '+p
 for label in LABELS:
  for domain in ['user/501','gui/501']:
   assert subprocess.run(['launchctl','print',domain+'/'+label],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0,'Already registered: '+label
 for port in [4510,8793,8797]:
  with socket.socket() as s:
   s.settimeout(2);assert s.connect_ex(('127.0.0.1',port))!=0,'Already listening'
 c=connect()
 try:
  assert c.execute("SELECT count(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0
  assert c.execute("SELECT count(*) FROM messages WHERE status IN ('queued','submitted')").fetchone()[0]==0
  assert c.execute("SELECT count(*) FROM messages WHERE status IN ('answered','failed') AND notify=1 AND receipt IS NULL").fetchone()[0]==0
  tables=ledger(c)
 finally:c.close()
 state=json.loads(STATE.read_text())
 assert not any(t.get('manager_v2') and t.get('current_status') in ['queued','running'] for t in state['tasks'].values())
 return tables,state

tables,state=preflight()
if sys.argv[1]=='backup':
 ROOT.mkdir(mode=0o700,parents=True,exist_ok=False)
 for p in list(HASHES)+[str(STATE)]:
  target=ROOT/Path(p).name;shutil.copy2(p,target);target.chmod(0o600);assert sha(target)==sha(p)
 c=connect();b=sqlite3.connect(str(ROOT/'manager.db'));c.backup(b);c.close()
 assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert ledger(b)==tables;b.close();(ROOT/'manager.db').chmod(0o600)
 cold=ROOT/'isolated-cold';cold.mkdir(mode=0o700)
 for p in list(ROOT.iterdir()):
  if p.is_file():shutil.copy2(p,cold/p.name);assert sha(p)==sha(cold/p.name)
 c=sqlite3.connect('file:'+str(cold/'manager.db')+'?mode=ro',uri=True);assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert ledger(c)==tables;c.close()
 manifest={p.name:sha(p) for p in ROOT.iterdir() if p.is_file()}
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backup_path':str(ROOT),'files':manifest,'ledger_hashes':tables,'cold_restore_verified':True,'pending_messages':0,'pending_deliveries':0,'active_projects':0,'bridge_queued_running':0,'production_started':False}
 (ROOT/'backup-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
elif sys.argv[1]=='restore':
 receipt=json.loads((ROOT/'backup-receipt.json').read_text());assert receipt['ledger_hashes']==tables
 for name,h in receipt['files'].items():assert sha(ROOT/name)==h
 assert json.loads((ROOT/'state.json').read_text())==state
 loaded=[]
 try:
  for label in LABELS:
   subprocess.run(['launchctl','bootstrap','user/501','/Users/herald/Library/LaunchAgents/'+label+'.plist'],check=True,capture_output=True);loaded.append(label)
   port={'com.windance.codex-app-server':4510,'com.windance.codex-bridge':8793,'com.windance.vega-manager':8797}[label]
   for attempt in range(20):
    with socket.socket() as s:
     s.settimeout(1)
     if s.connect_ex(('127.0.0.1',port))==0:break
    time.sleep(.5)
   else:raise RuntimeError('Listener did not start: '+label)
  time.sleep(12)
  health={}
  for port in [8791,8793,8797]:
   with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/health',timeout=5) as r:
    data=json.load(r);health[str(port)]={'http':r.status,**{k:data[k] for k in ['status','active','queued','busy'] if k in data}}
  assert health['8793'].get('active')==0 and health['8793'].get('queued')==0
  c=connect();assert ledger(c)==tables,'Ledger changed; reconcile before replay';tick=c.execute("SELECT value FROM state WHERE key='tick'").fetchone();c.close()
  assert tick and time.time()-float(tick[0])<20
  assert json.loads(STATE.read_text())==state,'Bridge state changed'
  result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'loaded':loaded,'domain':'user/501','health':health,'ledger_unchanged':True,'bridge_state_unchanged':True,'manager_tick_age_seconds':round(time.time()-float(tick[0]),2),'explicit_sends':0,'explicit_dispatches':0,'backup_path':str(ROOT)}
  (ROOT/'restoration-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 except Exception:
  for label in reversed(loaded):subprocess.run(['launchctl','bootout','user/501/'+label],capture_output=True)
  raise
else:raise ValueError('Unknown mode')
