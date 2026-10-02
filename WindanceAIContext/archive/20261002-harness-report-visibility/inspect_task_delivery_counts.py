import json,sqlite3
from pathlib import Path
p=Path('/Users/herald/.local/share/agent-harness/harness.db')
c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=1)
try:
 rows=c.execute('SELECT status,COUNT(*) FROM staff_task_deliveries GROUP BY status').fetchall()
 print(json.dumps({'legacy_status_counts':dict(rows),'new_journal_exists':(p.parent/'task-report-delivery.db').exists(),'content_read':False}))
finally:c.close()
