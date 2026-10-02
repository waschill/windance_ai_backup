"""Add separate report journal under stable idle predicates, then seal private archive."""
import hashlib,json,os,shutil,sqlite3,zipfile
from contextlib import closing
from pathlib import Path
os.umask(0o077)
root=Path('/Users/herald/backups/email-rebased-recovery-20261002T172133Z')
live=Path('/Users/herald/.local/share/agent-harness/harness.db')
journal=live.parent/'task-report-delivery.db'
def ro(p):return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=2)
def hashes(c):return {t:hashlib.sha256(json.dumps(c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall()).encode()).hexdigest() for t in ('staff_tasks','staff_task_runs','staff_task_deliveries','staff_task_revisions')}
with closing(ro(root/'snapshot.private.db')) as c:before=hashes(c)
def stable():
    with closing(ro(live)) as c:
        assert c.execute("SELECT count(*) FROM staff_tasks WHERE status IN ('pending','running','dispatching','in_progress')").fetchone()[0]==0
        assert hashes(c)==before
    with closing(ro(journal)) as c:
        assert c.execute('PRAGMA user_version').fetchone()[0]==1
        assert c.execute('SELECT count(*) FROM reports').fetchone()[0]==0
stable()
target=root/'task-report.private.db';assert not target.exists()
with closing(ro(journal)) as c,closing(sqlite3.connect(target)) as b:
    c.backup(b);b.execute('PRAGMA journal_mode=DELETE')
    assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and b.execute('SELECT count(*) FROM reports').fetchone()[0]==0
shutil.copyfile(target,root/'task-report-cold.private.db');stable()
m=json.loads((root/'manifest.private.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==d for n,d in m.items())
for p in (target,root/'task-report-cold.private.db'):m[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'manifest.private.json').write_text(json.dumps(m,indent=2))
archive=root/'email-rebased-private.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for name in list(m)+['manifest.private.json']:z.write(root/name,name)
print(json.dumps({'stable_files':len(m),'separate_report_journal':'schema1_empty','four_staff_tables_stable':True,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'live_writes':0}))
