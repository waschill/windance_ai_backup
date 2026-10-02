import hashlib,json,sqlite3,sys
from pathlib import Path
root=Path(sys.argv[1]);receipt=json.loads((root/'backup-receipt.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in receipt['files'].items())
c=sqlite3.connect((root/'cold.db').as_uri()+'?immutable=1',uri=True)
assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
for table,digest in receipt['protected_tables'].items():
    sql="SELECT * FROM state WHERE key!='tick' ORDER BY key" if table=='state_without_tick' else 'SELECT * FROM '+table+' ORDER BY rowid'
    assert hashlib.sha256(json.dumps(c.execute(sql).fetchall(),ensure_ascii=False).encode()).hexdigest()==digest
c.close()
(root/'hal-verification.json').write_text(json.dumps({'files':receipt['files'],'cold_restore_verified':True}))
print(json.dumps({'files_verified':len(receipt['files']),'protected_tables_verified':len(receipt['protected_tables']),'cold_integrity':'ok'}))
