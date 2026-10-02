"""Read private off-host snapshots; emit counts and verification results only."""
import hashlib,json,sqlite3
from pathlib import Path

root=Path(r'C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-webui-lab-precontainment')
results=[]
for name in ('truth-engine-lab',):
    target=root/name
    manifest=json.loads((target/'private-manifest.json').read_text(encoding='utf-8-sig'))
    for relative,expected in manifest['files'].items():
        assert hashlib.sha256((target/'data'/relative).read_bytes()).hexdigest()==expected
    for relative,tables in manifest['databases'].items():
        db=sqlite3.connect((target/'data'/relative).as_uri()+'?immutable=1',uri=True)
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        actual={}
        for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            quoted='"'+table.replace('"','""')+'"'
            rows=db.execute('SELECT * FROM '+quoted).fetchall()
            encoded=sorted(json.dumps(r,ensure_ascii=False,default=lambda v:{'bytes':v.hex()},separators=(',',':')) for r in rows)
            actual[table]={'count':len(rows),'sha256':hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
        assert actual==tables
        db.close()
    results.append({'container':name,'verified_files':len(manifest['files']),'verified_databases':len(manifest['databases']),
                    'all_file_hashes_match':True,'integrity_passed':True,'all_table_hashes_match':True})
print(json.dumps({'offhost_root':str(root),'results':results,'private_contents_exported':False},indent=2))

