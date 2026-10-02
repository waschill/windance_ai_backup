"""Fresh read-only snapshot and actual isolated startup for the exact email release."""
import asyncio,datetime,hashlib,importlib.util,json,os,secrets,shutil,sqlite3,sys
from contextlib import closing
from pathlib import Path
os.umask(0o077);sys.dont_write_bytecode=True
home=Path('/Users/herald');stage=Path('/tmp/email-rebased-private')
raw=(stage/'manifest.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='82422c5e1c180bad21df51a0397f306615f7f05a2952848010818edd9f23bc7c'
m=json.loads(raw);assert all(hashlib.sha256((stage/n).read_bytes()).hexdigest()==v for n,v in m.items())
assert json.loads((stage/'worker-policy.json').read_text())=={'manifest_sha256':digest}
live=home/'services/agent-harness/agent_harness.py'
assert hashlib.sha256(live.read_bytes()).hexdigest()=='c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7'
root=home/'backups'/('email-rebased-recovery-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));root.mkdir(mode=0o700)
release=root/'release';release.mkdir(mode=0o700)
for name in list(m)+['manifest.json','worker-policy.json']:shutil.copy2(stage/name,release/name)
shutil.copy2(live,root/'original.private.py')
with closing(sqlite3.connect((home/'.local/share/agent-harness/harness.db').as_uri()+'?mode=ro',uri=True)) as c,closing(sqlite3.connect(root/'snapshot.private.db')) as b:c.backup(b,pages=128,sleep=.05);b.execute("PRAGMA journal_mode=DELETE")
def tables(path):
 with closing(sqlite3.connect(path.resolve().as_uri()+'?immutable=1',uri=True)) as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  return {t:(c.execute('SELECT COUNT(*) FROM "'+t+'"').fetchone()[0],hashlib.sha256('\n'.join(sorted(repr(tuple(r)) for r in c.execute('SELECT * FROM "'+t+'"'))).encode()).hexdigest()) for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
before=tables(root/'snapshot.private.db')
def guard(event,args):
 if event in {'socket.connect','socket.bind','socket.sendto','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:raise RuntimeError('External effect denied during restoration')
 if event=='sqlite3.connect':assert str(root) in os.fsdecode(args[0]),'Non-fixture SQLite refused'
 if event=='open' and not isinstance(args[0],int):
  path,mode,flags=args
  if (flags or 0)&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):assert Path(os.fsdecode(path)).resolve().is_relative_to(root),'Non-fixture write refused'
sys.addaudithook(guard);sys.path.insert(0,str(release));checks=[]
def variant(label,source):
 scratch=root/(label+'-scratch');scratch.mkdir(mode=0o700);shutil.copy2(root/'snapshot.private.db',scratch/'harness.db')
 for name in ['DATA','CONFIG','LOG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
 os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch);os.environ['AGENT_HARNESS_TOKEN']=secrets.token_urlsafe(32)
 spec=importlib.util.spec_from_file_location('release_'+label,source);h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
 assert h.DB_FILE.resolve()==(scratch/'harness.db').resolve()
 h.TASK_REPORT_JOURNAL=scratch/'task-report-delivery.db'
 audits=[];h.audit=lambda event,*a,**k:audits.append(event)
 async def check():
  import httpx
  async with h.app.router.lifespan_context(h.app):
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://fixture') as client:
    health=await client.get('/health');assert health.status_code==200
    team=await client.get('/team',headers={'Authorization':'Bearer '+h.HARNESS_TOKEN});assert team.status_code==200
    if label=='candidate':
     denied=await client.post('/gmail/report',json={});assert denied.status_code==401
     h.HARNESS_TOKEN=''
     unavailable=await client.post('/gmail/report',json={});assert unavailable.status_code==503
     checks.extend([200,200,401,503])
 asyncio.run(check());assert audits==['startup']
 with closing(sqlite3.connect(scratch/'harness.db')) as c,closing(sqlite3.connect(root/(label+'.private.db'))) as b:c.backup(b);b.execute("PRAGMA journal_mode=DELETE")
 return tables(root/(label+'.private.db'))
baseline=variant('baseline',root/'original.private.py');candidate=variant('candidate',release/'agent_harness.py')
added={'email_action_intents','email_draft_recovery_evidence','email_approval_selections','email_approved_item_intents','email_mailbox_admission','email_undo_intents','email_sweep_cursor','email_sender_rule_receipts','email_rule_provenance'}
assert set(candidate)==set(before)|added
assert all(candidate[t]==v for t,v in baseline.items())
assert all(candidate[t]==v for t,v in before.items() if t!='sqlite_sequence')
assert all(candidate[t][0]==(1 if t=='email_sweep_cursor' else 0) for t in added)
shutil.copy2(root/'candidate.private.db',root/'cold.private.db');assert tables(root/'cold.private.db')==candidate
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in list(release.iterdir())+list(root.glob('*.private.*')) if p.is_file()}
(root/'manifest.private.json').write_text(json.dumps(files,indent=2))
print(json.dumps({'private_backup':str(root),'stable_files':len(files),'release_manifest':digest,'existing_nonsequence_tables_preserved':len(before)-1,
 'baseline_tables_match':True,'new_journals_empty_cursor_initialized':True,'cold_copy_match':True,'http_checks':checks,'external_effects':0,'production_changes':False,
 'limits':'Startup/read-only API only; no real account, provider, scheduled dispatch or deployment.'}))


