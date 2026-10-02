import hashlib,json,sqlite3,sys
from pathlib import Path
root=Path(sys.argv[1]);receipt=json.loads((root/'backup-receipt.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in receipt['files'].items())
for name in ('capture','sentinel'):
 with sqlite3.connect((root/(name+'.cold.db')).as_uri()+'?immutable=1',uri=True) as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and c.execute('PRAGMA user_version').fetchone()[0]==2
  assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0
(root/'hal-verification.json').write_text(json.dumps(receipt))
print(json.dumps({'verified_files':len(receipt['files']),'cold_journals_verified':2}))
