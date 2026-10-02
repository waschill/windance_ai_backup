"""Single-use guarded SAL intake deployment; never rewinds cursor or sends."""
import ast,hashlib,json,os,plistlib,re,sqlite3,subprocess,time
from pathlib import Path

backup=Path('/Users/zuzu/backups/sender-boundary-deploy-20261002T0016Z')
manifest=json.loads((backup/'manifest.json').read_text())
live=Path('/Users/zuzu/bin/imessage_herald_bridge.py');helper=live.parent/'bridge_sender_boundary.py'
state=Path('/Users/zuzu/.local/state/windance/imessage-herald-rowid')
plist=Path('/Users/zuzu/Library/LaunchAgents/com.windance.imessage-herald-bridge.plist')
label=f'gui/{os.getuid()}/com.windance.imessage-herald-bridge'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(digest(backup/name)==sha for name,sha in manifest.items())
assert digest(live)==manifest['bridge.original.py'] and not helper.exists()
assert digest(state)==manifest['cursor.original'] and digest(plist)==manifest['bridge.plist']
assert Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists()
for w in ['com.windance.supervisor','com.windance.supervisor-review']:
    assert subprocess.run(['launchctl','print',f'gui/{os.getuid()}/{w}'],capture_output=True).returncode!=0
def job():
    r=subprocess.run(['launchctl','print',label],capture_output=True,text=True,check=True)
    pid=re.search(r'(?m)^\s*pid = (\d+)',r.stdout)
    return int(pid.group(1)) if pid else None
before=job();assert before
outbox=Path('/Users/zuzu/.local/share/windance-imessage-outbox')
def counts():return {name:len(list((outbox/name).glob('*.json'))) for name in ['queue','inflight','uncertain']}
assert all(v==0 for v in counts().values())
with sqlite3.connect('file:/Users/zuzu/Library/Messages/chat.db?mode=ro',uri=True) as c:
    assert c.execute('SELECT count(*) FROM message WHERE is_from_me=0 AND text IS NOT NULL AND length(trim(text))>0 AND ROWID>?',(int(state.read_text()),)).fetchone()[0]==0
# Existing process retains original code until its one controlled restart.
for src,dst in [(backup/'bridge_sender_boundary.py',helper),(backup/'bridge.candidate.py',live)]:
    ast.parse(src.read_text())
    temporary=dst.with_name(dst.name+'.sender-boundary-new')
    with temporary.open('xb') as f:f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
    temporary.chmod(0o600 if dst==helper else 0o755)
    os.replace(temporary,dst)
subprocess.run(['launchctl','kickstart','-k',label],check=True,capture_output=True)
after=None
for _ in range(10):
    time.sleep(1);after=job()
    if after and after!=before:break
assert after and after!=before
time.sleep(3)
assert job()==after
assert digest(live)==manifest['bridge.candidate.py'] and digest(helper)==manifest['bridge_sender_boundary.py']
assert digest(plist)==manifest['bridge.plist']
# A natural incoming event would require separate reconciliation, not cursor restore.
assert digest(state)==manifest['cursor.original'], 'Cursor moved: reconcile natural activity, never rewind'
assert all(v==0 for v in counts().values()), 'Outbox changed: inspect before any further action'
receipt={'installed_source_sha256':digest(live),'installed_helper_sha256':digest(helper),'pid_changed':True,
 'stable_new_pid_after_seconds':3,'cursor_and_plist_unchanged':True,'outbox_counts':counts(),
 'warden_still_paused':Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists(),
 'scope':'Only Messages intake bridge restarted; no manual send or cursor rewind',
 'limits':'Natural future intake and independent transport delivery remain unverified'}
(backup/'deployment-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
