"""Independent read-only off-host verification, including nested release manifest."""
import datetime,hashlib,json,sqlite3,sys
from contextlib import closing
from pathlib import Path
root=Path(sys.argv[1]).resolve();m=json.loads((root/'manifest.private.json').read_text())
assert len(m)==39
for name,digest in m.items():
 p=(root/name).resolve();assert p.is_relative_to(root) and p.is_file()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
raw=(root/'release/manifest.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='82422c5e1c180bad21df51a0397f306615f7f05a2952848010818edd9f23bc7c'
assert json.loads((root/'release/worker-policy.json').read_text())=={'manifest_sha256':digest}
for name,h in json.loads(raw).items():assert hashlib.sha256((root/'release'/name).read_bytes()).hexdigest()==h
def tables(name):
 with closing(sqlite3.connect((root/name).as_uri()+'?immutable=1',uri=True)) as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  return {t:(c.execute('SELECT COUNT(*) FROM "'+t+'"').fetchone()[0],hashlib.sha256('\n'.join(sorted(repr(tuple(r)) for r in c.execute('SELECT * FROM "'+t+'"'))).encode()).hexdigest()) for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
before,baseline,after,cold=[tables(x+'.private.db') for x in ('snapshot','baseline','candidate','cold')]
added={'email_action_intents','email_draft_recovery_evidence','email_approval_selections','email_approved_item_intents','email_mailbox_admission','email_undo_intents','email_sweep_cursor','email_sender_rule_receipts','email_rule_provenance'}
assert set(after)==set(before)|added and all(after[t]==v for t,v in baseline.items())
assert all(after[t]==v for t,v in before.items() if t!='sqlite_sequence') and all(after[t][0]==(1 if t=='email_sweep_cursor' else 0) for t in added)
assert cold==after
for name in ('task-report.private.db','task-report-cold.private.db'):
 with closing(sqlite3.connect((root/name).as_uri()+'?immutable=1',uri=True)) as c:
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert c.execute('PRAGMA user_version').fetchone()[0]==1 and c.execute('SELECT count(*) FROM reports').fetchone()[0]==0
print(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stable_files_verified':len(m),
 'exact_release_and_policy_verified':True,'sqlite_integrity_checks':6,'task_report_journal_preserved':True,'existing_nonsequence_tables_preserved':len(before)-1,
 'cold_copy_tables_equal':True,'new_journals_empty_cursor_initialized':True,'production_changes':False}))


