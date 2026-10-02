"""Preflight excludes sensitive field contents and does not mutate disposable DB."""
import hashlib,json,sqlite3,tempfile
from pathlib import Path
from email_history_preflight import inspect
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'fixture.db';c=sqlite3.connect(p)
 c.executescript('CREATE TABLE approvals(action TEXT,status TEXT,payload_json TEXT);CREATE TABLE email_autonomy_actions(action TEXT,reason TEXT);')
 c.executemany('INSERT INTO approvals VALUES(?,?,?)',[('gmail_send','pending','PRIVATE_SENTINEL'),('gmail_send','executed','PRIVATE_SENTINEL'),('gmail_send','PRIVATE_SENTINEL','PRIVATE_SENTINEL'),('nonmail','pending','PRIVATE_SENTINEL')])
 c.executemany('INSERT INTO email_autonomy_actions VALUES(?,?)',[('action_outcome_unknown','PRIVATE_SENTINEL'),('trashed','PRIVATE_SENTINEL'),('error_left_untouched','PRIVATE_SENTINEL')]);c.commit();c.close()
 before=hashlib.sha256(p.read_bytes()).hexdigest();result=inspect(p)
 assert result['gmail_approval_status_counts']=={'executed':1,'pending':1,'other_unclassified':1}
 assert result['records_requiring_review_not_replay']==4 and result['migration_ready'] is False
 assert result['autonomy_action_counts']['error_left_untouched']==1
 assert before==hashlib.sha256(p.read_bytes()).hexdigest()
 c=sqlite3.connect(p);c.execute('INSERT INTO email_autonomy_actions VALUES(?,?)',('archived','PRIVATE_SENTINEL'));c.commit();c.close()
 updated=inspect(p)
 assert updated['autonomy_action_counts']['archived']==1 and updated['records_requiring_review_not_replay']==4
 assert 'PRIVATE_SENTINEL' not in json.dumps(result) and 'PRIVATE_SENTINEL' not in json.dumps(updated)
print(json.dumps({'private_sentinel_excluded':True,'unrelated_approvals_excluded':True,'unknown_status_requires_review':True,'snapshot_unchanged':True}))
