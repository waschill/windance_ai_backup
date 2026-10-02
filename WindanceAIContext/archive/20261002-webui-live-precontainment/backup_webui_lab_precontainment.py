"""Run inside existing WebUI container. Private online SQLite and stable-file copies."""
import hashlib,json,shutil,sqlite3
from pathlib import Path

source=Path('/app/backend/data');root=Path('/tmp/windance-webui-lab-precontainment-20261002T1816')
root.mkdir(mode=0o700,exist_ok=False);destination=root/'data';destination.mkdir(mode=0o700)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def table_hashes(c):
    results={}
    for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        quoted='"'+name.replace('"','""')+'"'
        rows=c.execute('SELECT * FROM '+quoted).fetchall()
        encoded=sorted(json.dumps(r,ensure_ascii=False,default=lambda v:{'bytes':v.hex()},separators=(',',':')) for r in rows)
        results[name]={'count':len(rows),'sha256':hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
    return results
manifest={};db_evidence={}
for p in sorted(source.rglob('*')):
    relative=p.relative_to(source)
    if relative.parts[0]=='cache' or not p.is_file() or p.name.endswith(('-wal','-shm')):continue
    if p.is_symlink():raise RuntimeError('Unexpected symlink in application data')
    target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
    with p.open('rb') as stream:is_sqlite=stream.read(16)==b'SQLite format 3\x00'
    if is_sqlite:
        original=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True);copy=sqlite3.connect(target)
        original.backup(copy)
        assert copy.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        expected=table_hashes(copy);copy.close()
        current=table_hashes(original);original.close()
        assert current==expected,'Source changed during backup; preserve attempt and reconcile'
        cold=sqlite3.connect('file:'+str(target)+'?immutable=1',uri=True)
        assert cold.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and table_hashes(cold)==expected;cold.close()
        db_evidence[str(relative)]=expected
    else:
        before=sha(p);shutil.copy2(p,target)
        assert sha(target)==before==sha(p),'File changed during copy'
    target.chmod(0o600);manifest[str(relative)]=sha(target)
# Every uploaded-file reference must resolve to included app data, without
# exporting names, identities or file contents into the public receipt.
c=sqlite3.connect('file:'+str(destination/'webui.db')+'?immutable=1',uri=True)
references=[r[0] for r in c.execute('SELECT path FROM file')];c.close()
for name in references:
    if not name:raise RuntimeError('Missing upload path')
    p=Path(name)
    relative=p.relative_to(source) if p.is_absolute() else p
    assert str(relative) in manifest and (destination/relative).is_file(),'Upload reference not captured'
(root/'private-manifest.json').write_text(json.dumps({'files':manifest,'databases':db_evidence},indent=2)+'\n')
print(json.dumps({'sqlite_databases':len(db_evidence),'stable_files':len(manifest),'uploaded_references_verified':len(references),
 'application_table_counts':{k:v['count'] for k,v in db_evidence['webui.db'].items() if k in ['user','chat','file','knowledge','memory','function','tool']},
 'integrity_and_table_hashes_verified':True,'cache_excluded':True,'runtime_not_stopped':True,'private_values_exported':False}))

