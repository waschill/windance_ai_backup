"""Scoped manager rollout with fresh off-host-verified backup and no replay."""
import ast,datetime,hashlib,json,os,re,shutil,sqlite3,subprocess,sys,time,urllib.request
from contextlib import closing
from pathlib import Path
from zoneinfo import ZoneInfo
os.umask(0o077)
home=Path('/Users/herald');service=home/'services/vega-manager';live=service/'manager.py'
stage=home/'backups/manager-receipt-release-20261002-r2/restored'
backup=home/'backups/manager-receipt-deploy-20261002'
database=home/'.local/share/vega-manager/manager.db'
bridge_state=home/'.local/share/windance-codex/state.json'
plist=home/'Library/LaunchAgents/com.windance.vega-manager.plist';label='user/501/com.windance.vega-manager'
helpers=['manager_receipt_delivery.py','receipt_report_transport.py','outbox_wire_protocol.py']
old='0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'
new='15cf1c789e1c1fcef837ed8ccc9e7df9525e73693d7ca9c15be1f279fb38d316'
candidate=stage/'manager_receipt_candidate_r2.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ro(p):return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=2)
def hashes(c):
    result={t:hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in ['projects','stages','events','messages']}
    result['state_without_tick']=hashlib.sha256(json.dumps(c.execute("SELECT * FROM state WHERE key!='tick' ORDER BY key").fetchall(),ensure_ascii=False).encode()).hexdigest()
    return result
def health(port):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=3) as r:assert r.status==200;return json.load(r)
def launch(*args,check=True):return subprocess.run(['launchctl',*args],check=check,capture_output=True,timeout=10)
def idle():
    b=health(8793);assert b['active']==0 and b['queued']==0,'Bridge busy'
    with closing(ro(database)) as c:
        assert c.execute("SELECT count(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0,'Active project'
        assert c.execute("SELECT count(*) FROM messages WHERE status IN ('queued','submitted','execution_uncertain') OR (status IN ('answered','failed') AND notify=1 AND receipt IS NULL)").fetchone()[0]==0,'Pending work/delivery'
        assert c.execute("SELECT count(*) FROM state WHERE key LIKE 'receipt-v2:%'").fetchone()[0]==0,'Receipt snapshots already present'
        result=hashes(c)
    state=json.loads(bridge_state.read_text())
    assert not any(t.get('manager_v2') and t.get('current_status') in ('queued','running','execution_uncertain') for t in state['tasks'].values())
    return result,sha(bridge_state)
def preflight():
    assert 5<=datetime.datetime.now(ZoneInfo('America/Denver')).hour<22
    assert sha(live)==old and sha(candidate)==new
    manifest=json.loads((stage/'release-manifest.json').read_text())
    assert all(sha(stage/n)==digest for n,digest in manifest.items())
    assert all(not (service/n).exists() for n in helpers)
    launch('print',label)
    receiver=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','SAL','python3','-B','/tmp/verify_installed_receipt_receiver.py'],capture_output=True,text=True,timeout=12)
    assert receiver.returncode==0 and json.loads(receiver.stdout)['warden_pause_preserved'],'Receiver or Warden preflight failed'
    assert health(8797)['status']=='ok'
    return idle()
before,bridge_hash=preflight();mode=sys.argv[1]
if mode=='backup':
    backup.mkdir(mode=0o700,exist_ok=False)
    files={'source.original.py':live,'source.candidate.py':candidate,'service.plist':plist,'bridge-state.json':bridge_state,**{n:stage/n for n in helpers}}
    for name,path in files.items():shutil.copyfile(path,backup/name)
    with closing(ro(database)) as c,closing(sqlite3.connect(backup/'manager.db')) as out:
        c.backup(out);out.execute('PRAGMA journal_mode=DELETE')
        assert out.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(out)==before
    shutil.copyfile(backup/'manager.db',backup/'cold.db')
    with closing(ro(backup/'cold.db')) as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(c)==before
    assert idle()==(before,bridge_hash)
    receipt={'files':{n:sha(backup/n) for n in list(files)+['manager.db','cold.db']},'protected_tables':before,'bridge_hash':bridge_hash,'cold_restore_verified':True}
    (backup/'backup-receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({'status':'backup_ready','files':len(receipt['files']),'protected_tables':len(before),'cold_restore_verified':True}))
elif mode=='deploy':
    receipt=json.loads((backup/'backup-receipt.json').read_text());verified=json.loads((backup/'hal-verification.json').read_text())
    assert verified['files']==receipt['files'] and verified['cold_restore_verified'] is True
    assert before==receipt['protected_tables'] and bridge_hash==receipt['bridge_hash']
    assert all(sha(backup/n)==v for n,v in receipt['files'].items())
    assert sha(plist)==receipt['files']['service.plist']
    for p in [candidate]+[stage/n for n in helpers]:ast.parse(p.read_text())
    def record(step):
        with (backup/'steps.jsonl').open('a') as f:f.write(json.dumps({'step':step,'at':time.time()})+'\n');f.flush();os.fsync(f.fileno())
    record('preflight_passed')
    registration=launch('print',label).stdout.decode()
    match=re.search(r'\bpid = (\d+)',registration);assert match,'Manager PID missing'
    previous_pid=int(match.group(1))
    launch('bootout',label);record('manager_unloaded')
    for _ in range(40):
        if launch('print',label,check=False).returncode!=0:break
        time.sleep(.1)
    else:raise RuntimeError('Manager registration removal unverified; inspect transition')
    for _ in range(40):
        try:os.kill(previous_pid,0)
        except ProcessLookupError:break
        time.sleep(.1)
    else:raise RuntimeError('Old manager PID remains; preserve stopped state and inspect')
    try:
        assert idle()==(before,bridge_hash),'Accepted state changed during stop'
    except Exception:
        # No source has changed: restore the original registration with its current ledger.
        launch('bootstrap','user/501',str(plist));record('original_registration_restored');raise
    for source,target in [(stage/n,service/n) for n in helpers]+[(candidate,live)]:
        temp=target.with_name(target.name+'.receipt-stage')
        with temp.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
        temp.chmod(0o600);os.replace(temp,target)
    record('sources_installed')
    started=time.time();launch('bootstrap','user/501',str(plist));record('manager_registered')
    for _ in range(40):
        try:
            h=health(8797)
            with closing(ro(database)) as c:tick=float(c.execute("SELECT value FROM state WHERE key='tick'").fetchone()[0])
            if h['status']=='ok' and tick>=started:break
        except Exception:pass
        time.sleep(.25)
    else:raise RuntimeError('New heartbeat unverified; preserve state and inspect partial deployment')
    assert idle()==(before,bridge_hash),'State changed; inspect without rollback'
    assert sha(live)==new and all(sha(service/n)==sha(stage/n) for n in helpers)
    assert sha(plist)==receipt['files']['service.plist']
    result={'status':'installed_healthy','source_sha256':sha(live),'helpers':3,'fresh_heartbeat':True,'protected_tables_and_state_unchanged':True,'bridge_state_unchanged':True,'service_definition_unchanged':True,'manual_sends':0,'dispatches':0,'legacy_records_not_adopted':True,'backup':str(backup)}
    record('verification_passed');(backup/'deployment-receipt.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
else:raise ValueError('unknown_mode')
