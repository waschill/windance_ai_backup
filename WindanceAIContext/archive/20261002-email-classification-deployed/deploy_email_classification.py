"""Source-only guarded rollout after separate off-host backup verification."""
import ast,datetime,hashlib,json,os,shutil,sqlite3,subprocess,sys,time,urllib.request
from contextlib import closing
from pathlib import Path
from zoneinfo import ZoneInfo
home=Path('/Users/herald');service=home/'services/agent-harness';live=service/'agent_harness.py'
candidate=home/'backups/email-classification-candidate-20261002/agent_harness.candidate.private.py'
helper=Path('/tmp/email_classification_contract.py');backup=home/'backups/email-classification-deploy-20261002T0300Z-r2'
db=home/'.local/share/agent-harness/harness.db';plist=home/'Library/LaunchAgents/com.windance.agent-harness.plist'
old='9865597bda4368784beac015dbcec712a271889395e9fcebf788c60b636774d4';new='0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0';helper_hash='3866fc9b9294b2e9f354c2f43ea0194616ebe0ec723fb133ba3fd4bd9bd236fc'
tables=['staff_tasks','staff_task_runs','staff_task_deliveries','staff_task_revisions','email_report_active','max_email_report_refs','email_autonomy_actions','approvals']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ro(p):return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
def hashes(c):return {t:hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in tables}
def health(port):
 with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=3) as r:assert r.status==200;return json.load(r)
def idle():
 b=health(8793);assert b['active']==0 and b['queued']==0
 with closing(ro(home/'.local/share/vega-manager/manager.db')) as c:
  assert c.execute("SELECT COUNT(*) FROM messages WHERE status IN ('queued','submitted','execution_uncertain') OR (status IN ('answered','failed') AND notify=1 AND receipt IS NULL)").fetchone()[0]==0
  assert c.execute("SELECT COUNT(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0
 with closing(ro(db)) as c:
  assert c.execute("SELECT COUNT(*) FROM staff_tasks WHERE status IN ('pending','running','dispatching')").fetchone()[0]==0
  return hashes(c)
def preflight():
 assert 5<=datetime.datetime.now(ZoneInfo('America/Denver')).hour<22
 assert sha(live)==old and sha(candidate)==new and sha(helper)==helper_hash
 assert not (service/'email_classification_contract.py').exists(),'Helper already present: inspect partial outcome, do not repeat'
 code="from pathlib import Path; import subprocess; assert Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists(); assert all(subprocess.run(['launchctl','print','gui/501/'+x],capture_output=True).returncode!=0 for x in ['com.windance.supervisor','com.windance.supervisor-review'])"
 subprocess.run(['ssh','-o','BatchMode=yes','SAL','/usr/bin/python3','-'],input=code.encode(),check=True,capture_output=True)
 subprocess.run(['launchctl','print','user/501/com.windance.agent-harness'],check=True,capture_output=True)
 health(8791);health(8797);return idle()
before=preflight();mode=sys.argv[1]
if mode=='backup':
 backup.mkdir(mode=0o700,exist_ok=False)
 for name,path in {'source.original.py':live,'source.candidate.py':candidate,'email_classification_contract.py':helper,'service.plist':plist}.items():
  shutil.copyfile(path,backup/name);(backup/name).chmod(0o600)
 with closing(ro(db)) as c,closing(sqlite3.connect(backup/'harness.db')) as b:
  c.backup(b);assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(b)==before
 (backup/'harness.db').chmod(0o600);shutil.copyfile(backup/'harness.db',backup/'cold.db');(backup/'cold.db').chmod(0o600)
 with closing(sqlite3.connect((backup/'cold.db').as_uri()+'?immutable=1',uri=True)) as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(c)==before
 assert idle()==before
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backup':str(backup),'files':{n:sha(backup/n) for n in ['source.original.py','source.candidate.py','email_classification_contract.py','service.plist','harness.db','cold.db']},'protected_tables':before,'cold_restore_verified':True}
 (backup/'backup-receipt.json').write_text(json.dumps(receipt,indent=2));(backup/'backup-receipt.json').chmod(0o600)
 print(json.dumps({'backup':str(backup),'files':receipt['files'],'cold_restore_verified':True,'protected_tables':len(before)}))
elif mode=='deploy':
 receipt=json.loads((backup/'backup-receipt.json').read_text());assert before==receipt['protected_tables']
 assert all(sha(backup/n)==h for n,h in receipt['files'].items())
 for p in [candidate,helper]:ast.parse(p.read_text())
 assert idle()==before
 for src,target in [(helper,service/helper.name),(candidate,live)]:
  temp=target.with_name(target.name+'.classification-stage')
  with temp.open('xb') as f:f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
  temp.chmod(0o600);os.replace(temp,target)
 subprocess.run(['launchctl','kickstart','-k','user/501/com.windance.agent-harness'],check=True,capture_output=True)
 healthy=False
 for _ in range(30):
  try:health(8791);healthy=True;break
  except Exception:time.sleep(.5)
 assert healthy,'Source installed but health unverified; inspect, never replay deployment'
 assert sha(live)==new and sha(service/helper.name)==helper_hash and sha(plist)==receipt['files']['service.plist']
 assert idle()==before,'New accepted records: reconcile, never rewind DB'
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':new,'helper_sha256':helper_hash,'health_http':200,'protected_tables_unchanged':True,'service_definition_unchanged':True,'backup':str(backup),'model_calls':0,'mailbox_actions':0,'sends':0}
 (backup/'deployment-receipt.json').write_text(json.dumps(result,indent=2));(backup/'deployment-receipt.json').chmod(0o600);print(json.dumps(result))
else:raise ValueError('Unknown mode')
