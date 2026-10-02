"""Guarded Harness caller deployment after separately verified private backup."""
from contextlib import closing
import ast,datetime,hashlib,json,os,shutil,sqlite3,subprocess,sys,time,urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
home=Path('/Users/herald');service=home/'services/agent-harness';live=service/'agent_harness.py'
release=home/'backups/report-callers-20261002-r2';stage=release/'restored'
candidate=stage/'harness_report_identity_r2.py';backup=home/'backups/harness-report-deploy-20261002'
database=home/'.local/share/agent-harness/harness.db';journal=database.parent/'task-report-delivery.db'
plist=home/'Library/LaunchAgents/com.windance.agent-harness.plist';label='user/501/com.windance.agent-harness'
helpers=['task_report_journal.py','task_report_status.py','daily_report_journal.py','receipt_report_transport.py','outbox_wire_protocol.py']
tables=['staff_tasks','staff_task_runs','staff_task_deliveries','staff_task_revisions','email_report_active','max_email_report_refs','email_autonomy_actions','approvals']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ro(p):return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=2)
def hashes(c):return {t:hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in tables}
def health(port):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=3) as r:assert r.status==200;return json.load(r)
def idle():
    bridge=health(8793);assert bridge['active']==0 and bridge['queued']==0
    with closing(ro(home/'.local/share/vega-manager/manager.db')) as c:
        assert c.execute("SELECT COUNT(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0
        assert c.execute("SELECT COUNT(*) FROM messages WHERE status IN ('queued','submitted','execution_uncertain') OR (status IN ('answered','failed') AND notify=1 AND receipt IS NULL)").fetchone()[0]==0
    with closing(ro(database)) as c:
        assert c.execute("SELECT COUNT(*) FROM staff_tasks WHERE status IN ('pending','running','dispatching','in_progress')").fetchone()[0]==0
        return hashes(c)
def preflight():
    assert 5<=datetime.datetime.now(ZoneInfo('America/Denver')).hour<22
    assert sha(live)=='0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0'
    assert sha(candidate)=='c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7'
    assert sha(release/'report-callers-private.zip')=='d830761e271aec2ae6cd95e21fa620334e69131792765731f556698de35134fa'
    manifest=json.loads((stage/'release-manifest.json').read_text())
    assert all(sha(stage/n)==manifest[n] and not (service/n).exists() for n in helpers)
    assert not journal.exists()
    subprocess.run(['launchctl','print',label],check=True,capture_output=True)
    receiver=subprocess.run(['ssh','-o','BatchMode=yes','SAL','python3','-B','/tmp/verify_installed_receipt_receiver.py'],capture_output=True,text=True,timeout=8)
    assert receiver.returncode==0 and json.loads(receiver.stdout)['warden_pause_preserved']
    health(8791);health(8797);return idle()
before=preflight();mode=sys.argv[1]
if mode=='backup':
    backup.mkdir(mode=0o700,exist_ok=False)
    files={'source.original.py':live,'source.candidate.py':candidate,'service.plist':plist,**{n:stage/n for n in helpers}}
    for name,path in files.items():shutil.copyfile(path,backup/name);(backup/name).chmod(0o600)
    with closing(ro(database)) as c,closing(sqlite3.connect(backup/'harness.db')) as out:
        c.backup(out);assert out.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(out)==before
    (backup/'harness.db').chmod(0o600);shutil.copyfile(backup/'harness.db',backup/'cold.db');(backup/'cold.db').chmod(0o600)
    with closing(sqlite3.connect((backup/'cold.db').as_uri()+'?immutable=1',uri=True)) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(c)==before
    assert idle()==before
    receipt={'files':{n:sha(backup/n) for n in list(files)+['harness.db','cold.db']},'protected_tables':before,'cold_restore_verified':True}
    (backup/'backup-receipt.json').write_text(json.dumps(receipt));(backup/'backup-receipt.json').chmod(0o600)
    print(json.dumps({'backup':str(backup),'files':len(receipt['files']),'protected_tables':len(before),'cold_restore_verified':True}))
elif mode=='deploy':
    receipt=json.loads((backup/'backup-receipt.json').read_text())
    verified=json.loads((backup/'hal-verification.json').read_text())
    assert verified['files']==receipt['files'] and verified['cold_restore_verified'] is True
    assert before==receipt['protected_tables'] and all(sha(backup/n)==v for n,v in receipt['files'].items())
    for n in helpers:ast.parse((stage/n).read_text())
    ast.parse(candidate.read_text())
    assert idle()==before
    sys.path.insert(0,str(stage));from task_report_journal import provision
    provision(journal)
    for source,target in [(stage/n,service/n) for n in helpers]+[(candidate,live)]:
        temp=target.with_name(target.name+'.report-stage')
        with temp.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
        temp.chmod(0o600);os.replace(temp,target)
    subprocess.run(['launchctl','kickstart','-k',label],check=True,capture_output=True,timeout=5)
    for attempt in range(30):
        try:health(8791);break
        except Exception:time.sleep(.5)
    else:raise RuntimeError('installed source health not verified; inspect partial outcome')
    assert sha(live)==sha(candidate) and all(sha(service/n)==sha(stage/n) for n in helpers)
    assert sha(plist)==receipt['files']['service.plist'] and idle()==before
    with closing(ro(journal)) as c:assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0
    result={'status':'installed_healthy','source_sha256':sha(live),'helpers':len(helpers),'protected_tables_unchanged':True,
            'service_definition_unchanged':True,'journal_empty':True,'manual_sends':0,'legacy_records_not_adopted':True,'backup':str(backup)}
    (backup/'deployment-receipt.json').write_text(json.dumps(result));print(json.dumps(result))
else:raise ValueError('unknown_mode')
