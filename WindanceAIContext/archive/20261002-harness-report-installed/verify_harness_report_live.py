"""Read-only installed HTTP metadata verification; never print task contents."""
from contextlib import closing
import hashlib,json,plistlib,sqlite3,urllib.request
from pathlib import Path
home=Path.home();db=home/'.local/share/agent-harness/harness.db'
source=home/'services/agent-harness/agent_harness.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7'
def ro(path):return sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
with closing(ro(db)) as c:
    row=c.execute("SELECT t.id FROM staff_tasks t JOIN staff_task_deliveries d ON d.task_id=t.id WHERE d.status='delivered' LIMIT 1").fetchone()
    before=dict(c.execute('SELECT status,COUNT(*) FROM staff_task_deliveries GROUP BY status').fetchall())
assert row is not None
config=plistlib.loads((home/'Library/LaunchAgents/com.windance.agent-harness.plist').read_bytes())
token=config.get('EnvironmentVariables',{}).get('AGENT_HARNESS_TOKEN','')
headers={'Authorization':'Bearer '+token} if token else {}
request=urllib.request.Request('http://127.0.0.1:8791/staff/tasks/'+str(row[0]),headers=headers)
with urllib.request.urlopen(request,timeout=3) as response:
    assert response.status==200;task=json.load(response)['task']
assert task['william_report_delivery']=={'state':'legacy_recorded','independent_receipt':False}
with closing(ro(db)) as c:assert dict(c.execute('SELECT status,COUNT(*) FROM staff_task_deliveries GROUP BY status').fetchall())==before
with closing(ro(db.parent/'task-report-delivery.db')) as c:assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0
print(json.dumps({'installed_task_http':200,'legacy_record_explicitly_unverified':True,'legacy_status_counts':before,
                  'new_journal_empty':True,'task_content_output':False,'sends':0,'history_changed':False}))
