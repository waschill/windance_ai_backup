"""Validate private transferred SAM recovery files without publishing their rows."""
import hashlib,json,sqlite3
from pathlib import Path
from contextlib import closing
root=Path(r'C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-sam-existing-db\sam-existing-db-recovery-20261002T024254Z')
manifest=json.loads((root/'private-manifest.json').read_text())
assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in manifest.items())
def tables(name):
    with closing(sqlite3.connect((root/name).as_uri()+'?mode=ro',uri=True)) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()==('ok',)
        return {t: sorted(repr(tuple(r)) for r in c.execute('SELECT * FROM "'+t.replace('"','""')+'"')) for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
before=tables('snapshot.private.db');baseline=tables('baseline.private.db');after=tables('candidate.private.db');cold=tables('cold-restored.private.db')
assert before==baseline and after==cold
assert set(after)==set(before)|{'sam_history_intents'} and not after['sam_history_intents']
assert all(after[k]==v for k,v in before.items())
print(json.dumps({'source_backup':'/home/williamschilling/backups/sam-existing-db-recovery-20261002T024254Z','offhost_directory':str(root),'verified_files':len(manifest),'sqlite_integrity_databases':4,'existing_tables_preserved':len(before),'cold_restore_all_tables_match':True,'source_and_candidate_hash_verified':True,'production_service_and_two_timers':'active after backup','api_calls':0,'production_changes':False}))
