import hashlib,json,sqlite3,sys
from pathlib import Path
root=Path(sys.argv[1]);receipt=json.loads((root/'backup-receipt.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in receipt['files'].items())
with sqlite3.connect((root/'cold.db').as_uri()+'?immutable=1',uri=True) as c:
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 for table,digest in receipt['protected_tables'].items():
  assert hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall(),ensure_ascii=False).encode()).hexdigest()==digest
(root/'hal-verification.json').write_text(json.dumps({'files':receipt['files'],'cold_restore_verified':True}))
print(json.dumps({'files_verified':len(receipt['files']),'protected_tables_verified':len(receipt['protected_tables']),'cold_integrity':'ok'}))
