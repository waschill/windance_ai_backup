"""Private source/database recovery archive; no live writes or dispatch."""
import hashlib,json,os,shutil,sqlite3,zipfile
from pathlib import Path
os.umask(0o077)
stage=Path('/Users/herald/backups/manager-receipt-staging-20261002')
root=Path('/Users/herald/backups/manager-receipt-release-20261002-r2')
root.mkdir(mode=0o700,exist_ok=False);bundle=root/'bundle';bundle.mkdir()
expected=json.loads((stage/'staging-manifest.json').read_text())
for name,digest in expected.items():
    assert Path(name).name==name
    data=(stage/name).read_bytes();assert hashlib.sha256(data).hexdigest()==digest,name
    (bundle/name).write_bytes(data)
originals={'original_manager.py':('/Users/herald/services/vega-manager/manager.py','0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'),
           'original_report.py':('/Users/herald/bin/windance_report_send.py','aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780')}
for name,(path,digest) in originals.items():
    data=Path(path).read_bytes();assert hashlib.sha256(data).hexdigest()==digest
    (bundle/name).write_bytes(data)
shutil.copyfile('/Users/herald/Library/LaunchAgents/com.windance.vega-manager.plist',bundle/'original_manager.plist')
src=sqlite3.connect('file:/Users/herald/.local/share/vega-manager/manager.db?mode=ro',uri=True)
dst=sqlite3.connect(bundle/'manager-snapshot.db')
src.backup(dst);dst.execute('PRAGMA journal_mode=DELETE');dst.close();src.close()
shutil.copyfile(bundle/'manager-snapshot.db',bundle/'manager-cold.db')
for name in ('manager-snapshot.db','manager-cold.db'):
    c=sqlite3.connect('file:'+str(bundle/name)+'?mode=ro',uri=True)
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';c.close()
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.iterdir())}
(bundle/'release-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2))
archive=root/'manager-receipt-private.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(bundle.iterdir()):z.write(p,p.name)
for name,(path,digest) in originals.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
print(json.dumps({'files':len(manifest),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'source_pins_unchanged':True,'database_integrity':'ok','live_mutations':0}))
