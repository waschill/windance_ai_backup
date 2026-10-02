"""Cold restore and hash/SQLite verification; never starts restored service."""
import hashlib,json,sqlite3,sys,zipfile
from pathlib import Path
archive=Path(sys.argv[1]);root=Path(sys.argv[2]);root.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:
    assert all(Path(n).name==n and '/' not in n and '\\' not in n for n in z.namelist())
    assert z.testzip() is None;z.extractall(root)
manifest=json.loads((root/'release-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
tables={}
for name in ('manager-snapshot.db','manager-cold.db'):
    c=sqlite3.connect('file:'+str(root/name)+'?mode=ro',uri=True)
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    tables[name]={t:hashlib.sha256(json.dumps(sorted(c.execute('SELECT * FROM '+t).fetchall(),key=repr),sort_keys=True).encode()).hexdigest() for t in ('projects','stages','events','messages','state')}
    c.close()
assert tables['manager-snapshot.db']==tables['manager-cold.db']
print(json.dumps({'status':'passed','files':len(manifest),'cold_table_equivalence':5,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'service_started':False}))
