"""One synthetic no-send rejection; output metadata only."""
import hashlib,json,sqlite3,urllib.request
from pathlib import Path
source=Path('/Users/herald/services/agent-harness/agent_harness.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='9865597bda4368784beac015dbcec712a271889395e9fcebf788c60b636774d4'
database=Path('/Users/herald/.local/share/agent-harness/harness.db')
def connect():return sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True)
with connect() as c:
 before=c.execute('SELECT count(*) FROM conversations').fetchone()[0]
 last=c.execute('SELECT coalesce(max(id),0) FROM audit_log').fetchone()[0]
marker='SYNTHETIC_MEMORY_GUARD_LIVE_20261002'
body={'message':'remember this: password: '+marker,'user':'William','channel':'vega-internal','request_id':'memory-guard-canary-20261002'}
req=urllib.request.Request('http://127.0.0.1:8791/message',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=10) as response:assert response.status==200;result=json.load(response)
assert result['model']=='memory-guard' and marker not in json.dumps(result)
with connect() as c:
 assert c.execute('SELECT count(*) FROM conversations').fetchone()[0]==before
 assert c.execute('SELECT count(*) FROM audit_log WHERE id>? AND payload_json LIKE ?',(last,'%'+marker+'%')).fetchone()[0]==0
 rows=c.execute("SELECT payload_json FROM audit_log WHERE id>? AND event_type='memory_rejected_secret_like'",(last,)).fetchall()
 assert any(json.loads(r[0])=={'reason':'secret_like_memory_content'} for r in rows)
print(json.dumps({'installed_http_rejection_passed':True,'content_free_rejection_audit':True,'marker_absent_from_new_audit':True,
 'conversation_count_unchanged':True,'synthetic_input_only':True,'model_calls':0,'sends':0,'real_secret_used':False}))
