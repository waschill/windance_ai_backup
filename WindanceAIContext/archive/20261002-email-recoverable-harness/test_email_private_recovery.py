"""Private online snapshot and full candidate ASGI lifecycle; no external effects."""
import asyncio,datetime,hashlib,importlib.util,json,os,shutil,sqlite3,sys
from contextlib import closing
from pathlib import Path
os.umask(0o077)
home=Path('/Users/herald');stage=home/'backups/email-recoverable-candidate-20261002'
source=stage/'agent_harness.candidate.private.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='0f04b4a436e2f9ea46f8545222d333ce5abe86f3be7aba43e22d2f1b7de4a1f9'
manifest=json.loads((stage/'manifest.json').read_text())
assert all(hashlib.sha256((stage/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
live=home/'services/agent-harness/agent_harness.py'
assert hashlib.sha256(live.read_bytes()).hexdigest()=='0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0'
root=home/'backups'/('email-private-recovery-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));root.mkdir(mode=0o700)
with closing(sqlite3.connect((home/'.local/share/agent-harness/harness.db').as_uri()+'?mode=ro',uri=True)) as c,closing(sqlite3.connect(root/'snapshot.private.db')) as b:c.backup(b,pages=128,sleep=.05)
for src,name in [(source,'candidate.private.py'),(live,'original.private.py'),(stage/'email_action_intent.py','email_action_intent.py'),(stage/'gmail_draft_recovery.py','gmail_draft_recovery.py')]:shutil.copyfile(src,root/name)
def hashes(path):
 with closing(sqlite3.connect(path.as_uri()+'?immutable=1',uri=True)) as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  return {t:hashlib.sha256('\n'.join(sorted(repr(tuple(r)) for r in c.execute('SELECT * FROM "'+t.replace('"','""')+'"'))).encode()).hexdigest() for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
before=hashes(root/'snapshot.private.db')
sys.path[:0]=[str(stage),str(home/'services/agent-harness')]
def guard(event,args):
 if event in {'socket.connect','subprocess.Popen','os.system','os.posix_spawn'}:raise RuntimeError('External operation denied in isolated recovery')
sys.addaudithook(guard)
def verify_variant(label,app_source):
 scratch=root/label;scratch.mkdir(mode=0o700);shutil.copyfile(root/'snapshot.private.db',scratch/'harness.db')
 for name in ['DATA','LOG','CONFIG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
 os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch)
 spec=importlib.util.spec_from_file_location('email_recovery_'+label,app_source);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
 assert h.DB_FILE.resolve()==(scratch/'harness.db').resolve()
 effects=[];audits=[]
 def forbidden(*a,**k):effects.append('denied');raise AssertionError('Mailbox/model/dispatch forbidden')
 for name in ['gmail_service','model_reply','dispatch_staff_worker']:setattr(h,name,forbidden)
 h.audit=lambda event,*a,**k:audits.append(event)
 async def run():
  import httpx
  async with h.app.router.lifespan_context(h.app):
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',4567)),base_url='http://fixture') as client:
    response=await client.get('/health');assert response.status_code==200
 asyncio.run(run());assert audits==['startup'] and not effects
 with closing(sqlite3.connect(scratch/'harness.db')) as c,closing(sqlite3.connect(root/(label+'.private.db'))) as b:
  c.backup(b);assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 return hashes(root/(label+'.private.db'))
baseline=verify_variant('baseline',live);after=verify_variant('candidate',source)
assert set(after)==set(before)|{'email_action_intents','email_draft_recovery_evidence'}
assert all(after[t]==v for t,v in baseline.items())
assert all(after[t]==v for t,v in before.items() if t!='sqlite_sequence')
with closing(sqlite3.connect((root/'candidate.private.db').as_uri()+'?immutable=1',uri=True)) as c:
 assert c.execute('SELECT COUNT(*) FROM email_action_intents').fetchone()[0]==0
 assert c.execute('SELECT COUNT(*) FROM email_draft_recovery_evidence').fetchone()[0]==0
shutil.copyfile(root/'candidate.private.db',root/'cold.private.db');assert hashes(root/'cold.private.db')==after
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.private.json').write_text(json.dumps(files,indent=2))
print(json.dumps({'private_backup':str(root),'files_sha256':files,'existing_nonsequence_tables_preserved':len(before)-1,'all_existing_tables_match_baseline_startup':True,'sequence_change_matches_baseline':True,'full_module_and_asgi_lifespan':True,'health_http':200,'lifecycle_audit_intercepted':['startup'],'cold_restore_all_tables_match':True,'actual_external_calls':0,'production_changes':False,'limits':'Audit intercepted; no real TCP, Google credentials, background worker, mailbox report or authoritative reconciliation exercised'}))
