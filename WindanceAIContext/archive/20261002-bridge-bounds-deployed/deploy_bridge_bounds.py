"""Guarded coordinated source rollout; no model call, send or job submission."""
import ast,datetime,hashlib,json,os,plistlib,shutil,sqlite3,subprocess,sys,time,urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
home=Path('/Users/herald');stage=home/'services/bridge-bounds-20261002';backup=home/'backups/bridge-bounds-deploy-20261002T0112Z'
db=home/'.local/share/vega-manager/manager.db';statefile=home/'.local/share/windance-codex/state.json'
live={'bridge':home/'services/windance-codex-bridge/server.mjs','manager':home/'services/vega-manager/manager.py'}
candidates={'bridge':stage/'server-candidate.mjs','manager':stage/'manager-candidate.py'}
old={'bridge':'62483284dea6eefe010ea9d34cc4bb4438a6042bb910462f8679ab676ef80c1c','manager':'1d2c67417ca4080158db8e5c9840b5c602523856bfc7551ad0f2c8276a4c7a83'}
new={'bridge':'ad07a207e2dfdd84c226fedc1a8c65cf942bf69b0c6fe1b41a9deac35085508e','manager':'0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'}
labels={'bridge':'com.windance.codex-bridge','manager':'com.windance.vega-manager'}
plists={k:home/'Library/LaunchAgents'/f'{v}.plist' for k,v in labels.items()}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def conn(path):return sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
def tables(c):return {t:hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in ['projects','stages','events','messages']}
def launch(*args,check=True):return subprocess.run(['launchctl',*args],check=check,capture_output=True)
def health(port):
 with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=3) as r:assert r.status==200;return json.load(r)
def idle():
 with conn(db) as c:
  assert c.execute("SELECT COUNT(*) FROM messages WHERE status IN ('queued','submitted','execution_uncertain')").fetchone()[0]==0,'Manager work present'
  assert c.execute("SELECT COUNT(*) FROM messages WHERE status IN ('answered','failed') AND notify=1 AND receipt IS NULL").fetchone()[0]==0,'Pending delivery'
  assert c.execute("SELECT COUNT(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0,'Active project'
  hashes=tables(c)
 state=json.loads(statefile.read_text())
 assert not any(t.get('manager_v2') and t.get('current_status') in ['queued','running','execution_uncertain'] for t in state['tasks'].values()),'Bridge work present'
 return hashes,state
def common():
 assert 5<=datetime.datetime.now(ZoneInfo('America/Denver')).hour<22,'Protected hours'
 for k in live:assert sha(live[k])==old[k] and sha(candidates[k])==new[k],'Source drift'
 for k in plists:
  assert plistlib.loads(plists[k].read_bytes())['Label']==labels[k]
  launch('print','user/501/'+labels[k])
 code="from pathlib import Path; import subprocess; assert Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists(); assert all(subprocess.run(['launchctl','print','gui/501/'+x],capture_output=True).returncode!=0 for x in ['com.windance.supervisor','com.windance.supervisor-review'])"
 subprocess.run(['ssh','SAL','/usr/bin/python3','-'],input=code.encode(),check=True,capture_output=True)
 bh=health(8793);assert bh['active']==0 and bh['queued']==0
 health(8797);return idle()
def write_source(key,path):
 target=live[key].with_name(live[key].name+'.bounds-staged')
 with target.open('xb') as f:f.write(path.read_bytes());f.flush();os.fsync(f.fileno())
 target.chmod(live[key].stat().st_mode&0o777);os.replace(target,live[key])
def wait_health(port):
 for _ in range(25):
  try:return health(port)
  except Exception:time.sleep(.3)
 raise RuntimeError('Service health failed')
mode=sys.argv[1];protected,original_state=common()
if mode=='backup':
 backup.mkdir(mode=0o700,exist_ok=False)
 files={**{k+'.original':v for k,v in live.items()},**{k+'.candidate':v for k,v in candidates.items()},**{k+'.plist':v for k,v in plists.items()},'bridge-state.json':statefile}
 for name,path in files.items():shutil.copy2(path,backup/name);(backup/name).chmod(0o600);assert sha(backup/name)==sha(path)
 with conn(db) as c,sqlite3.connect(backup/'manager.db') as b:
  c.backup(b);assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and tables(b)==protected
 shutil.copy2(backup/'manager.db',backup/'manager-cold.db')
 with sqlite3.connect('file:'+str(backup/'manager-cold.db')+'?immutable=1',uri=True) as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and tables(c)==protected
 ast.parse((backup/'manager.original').read_text());ast.parse((backup/'manager.candidate').read_text())
 assert json.loads((backup/'bridge-state.json').read_text())==original_state
 assert idle()==(protected,original_state)
 names=list(files)+['manager.db','manager-cold.db']
 for name in names:(backup/name).chmod(0o600)
 receipt={'backup':str(backup),'files':{n:sha(backup/n) for n in names},'protected_tables':protected,'cold_verified':True,'production_changed':False}
 (backup/'backup-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
elif mode=='deploy':
 receipt=json.loads((backup/'backup-receipt.json').read_text())
 assert all(sha(backup/n)==h for n,h in receipt['files'].items())
 assert protected==receipt['protected_tables'] and sha(statefile)==receipt['files']['bridge-state.json']
 for k in plists:assert sha(plists[k])==receipt['files'][k+'.plist']
 # Stop intake to this controller first; SAL retains unacknowledged inbound work.
 stopped=[]
 try:
  for k in ['manager','bridge']:
   launch('bootout','user/501/'+labels[k]);stopped.append(k)
   assert idle()==(protected,original_state),'Work changed during stop; preserve state'
  for k in ['bridge','manager']:write_source(k,candidates[k])
  launch('bootstrap','user/501',str(plists['bridge']));wait_health(8793)
  launch('bootstrap','user/501',str(plists['manager']));wait_health(8797)
  # Require a fresh manager heartbeat after startup, without submitting any work.
  for _ in range(25):
   mh=health(8797)
   if mh.get('tick_age_seconds') is not None and mh['tick_age_seconds']<15:break
   time.sleep(.3)
  else:raise RuntimeError('Manager heartbeat not verified')
  assert idle()==(protected,original_state),'New work appeared; inspect rather than rewind'
  assert all(sha(live[k])==new[k] for k in live)
  result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'installed_hashes':new,'health_200':True,'fresh_manager_heartbeat':True,
    'protected_tables_unchanged':True,'bridge_state_unchanged':True,'definitions_unchanged':all(sha(plists[k])==receipt['files'][k+'.plist'] for k in plists),
    'backup':str(backup),'model_calls':0,'job_submissions':0,'sends':0}
  (backup/'deployment-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 except Exception:
  # Rollback source only when no accepted/new/uncertain work makes that unsafe.
  if idle()==(protected,original_state):
   for k in ['manager','bridge']:launch('bootout','user/501/'+labels[k],check=False)
   for k in live:
    if sha(live[k])!=old[k]:write_source(k,backup/(k+'.original'))
   for k,port in [('bridge',8793),('manager',8797)]:launch('bootstrap','user/501',str(plists[k]));wait_health(port)
  raise
else:raise ValueError('Unknown mode')
