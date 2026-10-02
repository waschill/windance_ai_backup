"""One-time guarded SAL receiver-only cutover. Never sends a manual message."""
import datetime,hashlib,json,os,plistlib,re,select,shutil,sqlite3,subprocess,sys,time
from pathlib import Path
from zoneinfo import ZoneInfo
from receiver_pause_guard import inspect
home=Path('/Users/zuzu');root=home/'.local/share/windance-imessage-outbox'
runtime=home/'services/receipt-outbox';release=home/'backups/receipt-release-20261002-r3'
backup=home/'backups/outbox-preintegration-20261002T151715Z'
launch=home/'Library/LaunchAgents/com.windance.imessage-outbox.plist'
candidate=home/'backups/receipt-launch-candidate-20261002/candidate.plist'
record=home/'backups/receipt-install-20261002';target='gui/501/com.windance.imessage-outbox'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def job():return subprocess.run(['launchctl','print',target],capture_output=True,text=True,timeout=3)
def pid_of(result):return int(re.search(r'(?m)^\s*pid = (\d+)',result.stdout).group(1))
def busy():return any(any((root/n).iterdir()) for n in ('queue','inflight','uncertain') if (root/n).exists())
def record_step(step,**fields):
    with (record/'steps.jsonl').open('a') as f:
        f.write(json.dumps({'at':time.time(),'step':step,**fields})+'\n');f.flush();os.fsync(f.fileno())

assert Path.home()==home and os.getuid()==501
assert sha(Path(__file__).with_name('receiver_pause_guard.py'))=='8029178794b95c4a850b9ebd5b6bf463a3fdfd41d2342fbcdc79a0faa5a0ff7a'
assert 5<=datetime.datetime.now(ZoneInfo('America/Denver')).hour<22
assert (home/'services/windance-supervisor/PAUSED').exists()
assert all(subprocess.run(['launchctl','print','gui/501/'+label],capture_output=True).returncode!=0 for label in ('com.windance.supervisor','com.windance.supervisor-review'))
assert not runtime.exists() and not (root/'journal.db').exists() and not record.exists()
assert sha(launch)=='d1f6f9555b68822540ad6eb67531fba100156f21a00131abad0d417083a04692'
assert sha(candidate)=='28c0a98eeec1321eff1d5f7d9ea5b4bd503deef55dfe412dadbc1ffcd3b1e9f8'
assert sha(home/'bin/imessage_outbox_daemon.py')=='f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'
assert sha(home/'bin/send_imessage_payload.py')=='382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f'
assert sha(release/'receipt-release-r3.zip')=='56066b9fe1a65471b2ab44bd1fe6de66677bf72a060eff40011b52c65dd0d7f5'
assert sha(backup/'outbox-private.zip')=='14c480b1b6617b67977da4949939e9cb7b14d01bd68c6071ee77a15ccda3f2f0'
saved=json.loads((backup/'private-manifest.json').read_text())
def same_saved_state():
    current={str(p.relative_to(root)):sha(p) for folder in ('queue','claims','results','inflight','uncertain') for p in (root/folder).glob('*.json')}
    expected={k[6:]:v for k,v in saved.items() if k.startswith('state/')}
    return current==expected
assert same_saved_state() and not busy(),'live state changed; fresh backup required'
assert json.loads((home/'backups/receipt-gui-access-20261002/result.json').read_text())['readable'] is True
check="""import sqlite3
from pathlib import Path
c=sqlite3.connect((Path.home()/'.local/share/vega-manager/manager.db').as_uri()+'?mode=ro',uri=True)
assert c.execute("SELECT COUNT(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0
assert c.execute("SELECT COUNT(*) FROM messages WHERE status IN ('queued','submitted','execution_uncertain') OR (status IN ('answered','failed') AND notify=1 AND receipt IS NULL)").fetchone()[0]==0
print('idle')
"""
control=subprocess.run(['ssh','HERALD','/Users/herald/.hermes/hermes-agent/venv/bin/python','-'],input=check,text=True,capture_output=True,timeout=10)
assert control.returncode==0 and control.stdout.strip()=='idle','manager work or unreadable ownership'
old=job();assert old.returncode==0;old_pid=pid_of(old)
old_identity=inspect(old_pid);assert old_identity is not None and 'T' not in old_identity[1]
old_command=subprocess.run(['/bin/ps','-p',str(old_pid),'-o','command='],capture_output=True,text=True,timeout=2).stdout
assert str(home/'bin/imessage_outbox_daemon.py') in old_command
record.mkdir(mode=0o700);shutil.copyfile(launch,record/'original.plist');shutil.copyfile(candidate,record/'candidate.plist')
record_step('preflight_passed',old_pid=old_pid,backup_matches_live=True)
runtime.mkdir(mode=0o700)
manifest=json.loads((release/'restored/release-manifest.json').read_text())
installed={}
for name,digest in manifest.items():
    if (name.endswith('.py') and not name.startswith(('test_','original_'))) or name.endswith('.whl'):
        source=release/'restored'/name;assert sha(source)==digest
        shutil.copyfile(source,runtime/name);(runtime/name).chmod(0o600);installed[name]=digest
(runtime/'runtime-manifest.json').write_text(json.dumps(installed,sort_keys=True))
sys.path.insert(0,str(runtime))
from message_receipt_journal import Journal
os.umask(0o077);Journal(root/'journal.db',create=True)
shutil.copyfile(root/'journal.db',record/'empty-journal.db')
record_step('runtime_staged',runtime_files=len(installed))
assert same_saved_state() and not busy(),'work arrived before pause; no service change'
guard=None
try:
    python=plistlib.loads(launch.read_bytes())['ProgramArguments'][0]
    guard=subprocess.Popen([python,'-B',str(Path(__file__).with_name('receiver_pause_guard.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
    guard.stdin.write((json.dumps({'pid':old_pid,'identity':old_identity[0],'seconds':15})+'\n').encode());guard.stdin.flush()
    assert select.select([guard.stdout],[],[],3)[0]
    assert json.loads(guard.stdout.readline())['status']=='paused'
    assert not busy(),'busy while paused; resume unchanged'
    stopped=inspect(old_pid)
    assert guard.poll() is None and stopped is not None and stopped[0]==old_identity[0] and 'T' in stopped[1]
    record_step('idle_paused')
    subprocess.run(['launchctl','bootout',target],check=True,capture_output=True,timeout=10)
    assert job().returncode!=0
    deadline=time.monotonic()+2
    while inspect(old_pid) is not None and time.monotonic()<deadline:time.sleep(.05)
    assert inspect(old_pid) is None,'old process still present'
    record_step('old_receiver_removed')
finally:
    if guard is not None:
        if guard.stdin and not guard.stdin.closed:guard.stdin.close()
        guard.wait(timeout=4);guard.stdout.close()
temporary=launch.with_suffix('.receipt-tmp');temporary.write_bytes(candidate.read_bytes());os.chmod(temporary,0o644);os.replace(temporary,launch)
record_step('service_definition_replaced')
subprocess.run(['launchctl','bootstrap','gui/501',str(launch)],check=True,capture_output=True,timeout=5)
deadline=time.monotonic()+5;health=None
while time.monotonic()<deadline:
    current=job()
    if current.returncode==0 and (root/'dispatcher-status.json').exists():
        health=json.loads((root/'dispatcher-status.json').read_text())
        if health.get('pid')==pid_of(current) and health.get('state')=='idle' and time.time()-health.get('observed_unix',0)<5:break
    time.sleep(.1)
else:raise RuntimeError('new_receiver_health_unverified; preserve history and investigate')
assert sha(launch)==sha(candidate) and all(sha(runtime/n)==v for n,v in installed.items())
with sqlite3.connect((root/'journal.db').as_uri()+'?mode=ro',uri=True) as c:
    assert c.execute('PRAGMA user_version').fetchone()[0]==3
    new_requests=c.execute('SELECT COUNT(*) FROM requests').fetchone()[0]
result={'status':'installed_healthy','pid':health['pid'],'old_pid_gone':True,'same_label':True,
        'runtime_files':len(installed),'previous_state_unchanged':same_saved_state(),'new_contract_requests':new_requests,
        'manual_sends':0,'callers_changed':False,'recovery_path':str(record)}
(record/'result.json').write_text(json.dumps(result));record_step('verified',**result);print(json.dumps(result))
