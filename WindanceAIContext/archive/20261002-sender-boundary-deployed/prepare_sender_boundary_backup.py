"""Fresh private SAL source/cursor/plist backup; no production mutation."""
import ast,hashlib,json,os,plistlib,shutil,sqlite3,subprocess
from pathlib import Path

live=Path('/Users/zuzu/bin/imessage_herald_bridge.py')
candidate=Path('/Users/zuzu/backups/sender-boundary-candidate-20261002')
state=Path('/Users/zuzu/.local/state/windance/imessage-herald-rowid')
plist=Path('/Users/zuzu/Library/LaunchAgents/com.windance.imessage-herald-bridge.plist')
backup=Path('/Users/zuzu/backups/sender-boundary-deploy-20261002T0016Z')
assert hashlib.sha256(live.read_bytes()).hexdigest()=='0b4753c2823be856d2124566e04e59108f346309d301c9b6cf00962d6418ed4a'
assert hashlib.sha256((candidate/'imessage_herald_bridge.py').read_bytes()).hexdigest()=='e90460b83533ecab7332dd0f7b78a122419c9325a6e24c777f98b5c5f92c632a'
assert Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists()
for label in ['com.windance.supervisor','com.windance.supervisor-review']:
    assert subprocess.run(['launchctl','print',f'gui/{os.getuid()}/{label}'],capture_output=True).returncode!=0
assert subprocess.run(['launchctl','print',f'gui/{os.getuid()}/com.windance.imessage-herald-bridge'],capture_output=True).returncode==0
outbox=Path('/Users/zuzu/.local/share/windance-imessage-outbox')
assert all(not list((outbox/x).glob('*.json')) for x in ['queue','inflight','uncertain'])
with sqlite3.connect('file:/Users/zuzu/Library/Messages/chat.db?mode=ro',uri=True) as c:
    assert c.execute('SELECT count(*) FROM message WHERE is_from_me=0 AND text IS NOT NULL AND length(trim(text))>0 AND ROWID>?',(int(state.read_text()),)).fetchone()[0]==0
assert not (live.parent/'bridge_sender_boundary.py').exists()
backup.mkdir(mode=0o700,exist_ok=False)
for name,path in {'bridge.original.py':live,'cursor.original':state,'bridge.plist':plist,
 'bridge.candidate.py':candidate/'imessage_herald_bridge.py','bridge_sender_boundary.py':candidate/'bridge_sender_boundary.py'}.items():
    shutil.copy2(path,backup/name);(backup/name).chmod(0o600)
    assert (backup/name).read_bytes()==path.read_bytes()
for p in backup.glob('*.py'):ast.parse(p.read_text())
assert plistlib.loads((backup/'bridge.plist').read_bytes())['Label']=='com.windance.imessage-herald-bridge'
assert int((backup/'cursor.original').read_text())>=0
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in backup.iterdir()}
(backup/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'backup':str(backup),'files':manifest,'cold_source_plist_cursor_checks':'passed','queue_and_pending_empty':True,'production_changed':False},indent=2))
