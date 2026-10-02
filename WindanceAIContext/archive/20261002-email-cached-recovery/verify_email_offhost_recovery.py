"""Read-only independent HAL verification; emits no private rows or source."""
import datetime, hashlib, json, sqlite3, sys
from contextlib import closing
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv)>1 else Path(r'C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-recoverable')
manifest = json.loads((root / 'manifest.private.json').read_text())
cached_package=len(sys.argv)>2 and sys.argv[2]=='--cached-package'
transport_package=cached_package or (len(sys.argv)>2 and sys.argv[2]=='--transport-package')
undo_package=transport_package or (len(sys.argv)>2 and sys.argv[2]=='--undo-package')
assert len(manifest) == (17 if cached_package else 16 if transport_package else 15 if undo_package else 8)
if transport_package:
    assert manifest['candidate.private.py']==('61028799755ebc22d823a56da155adf0489cdceefb1669ac973c25a97df2ef93' if cached_package else '30ec0a37df1ac30ece7649eb1bbb66f24d290d4477e60d6ff98b9d02b87e7794')
    assert manifest['gmail_single_attempt_transport.py']=='5753b6c3b9ac59021b2de6480656d167502d550e61254633aff09e4197a05c12'
if cached_package:assert manifest['gmail_credential_cache.py']=='2c50a126b771a12cae668d74de3bdf3dd969fe29134329ae6d9fb1cb42440803'
for name, expected in manifest.items():
    path = (root / name).resolve()
    assert path.parent == root.resolve()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected

def inspect(name):
    path = root / name
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        tables = {}
        for (table,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            rows = conn.execute('SELECT * FROM "' + table.replace('"', '""') + '"').fetchall()
            tables[table] = (len(rows), hashlib.sha256('\n'.join(sorted(repr(tuple(row)) for row in rows)).encode()).hexdigest())
        return tables

snapshot, baseline, candidate, cold = [inspect(n + '.private.db') for n in ('snapshot', 'baseline', 'candidate', 'cold')]
added = {'email_action_intents', 'email_draft_recovery_evidence'}
if undo_package:added|={'email_approval_selections','email_approved_item_intents','email_mailbox_admission','email_undo_intents'}
assert set(candidate) == set(snapshot) | added
assert all(candidate[t] == value for t, value in baseline.items())
assert all(candidate[t] == value for t, value in snapshot.items() if t != 'sqlite_sequence')
assert all(candidate[t][0] == 0 for t in added)
assert cold == candidate
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in manifest.items())
print(json.dumps({'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': 'HAL', 'stable_files_verified': len(manifest), 'sqlite_integrity_passes': 4, 'existing_nonsequence_tables_preserved': len(snapshot) - 1, 'all_original_tables_match_baseline_startup': True, 'cold_tables_match_candidate': True, 'new_recovery_tables_empty': True, 'backup_files_unchanged': True, 'production_changes': False, 'application_model_calls': 0, 'limits': 'Offline immutable copies only; no service startup, Gmail transport, authentication, historical restore reconciliation or full host recovery certified.'}, indent=2))
