"""Read-only metadata, never mailbox content or message identifiers."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3

home = Path.home()
source = (home/'services/agent-harness/agent_harness.py').read_text()
tree = ast.parse(source)
names = {'save_email_report_refs','latest_email_ref_map','consume_latest_email_ref_map',
         'prepare_gmail_report_reply_actions','gmail_autonomy_report','undo_email_autonomy_action'}
out = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
       'functions': {n.name: hashlib.sha256(ast.get_source_segment(source,n).encode()).hexdigest()
                     for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names}}
conn = sqlite3.connect('file:'+str(home/'.local/share/agent-harness/harness.db')+'?mode=ro', uri=True)
conn.execute('pragma query_only=ON')
conn.execute('begin')
tables = {'email_report_active','max_email_report_refs','max_email_report_consumed','email_autonomy_actions'}
found = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
out['tables'] = {}
for table in sorted(tables & found):
    columns = [r[1] for r in conn.execute('pragma table_info("'+table+'")')]
    out['tables'][table] = {'columns':columns, 'count':conn.execute('select count(*) from "'+table+'"').fetchone()[0]}
active = conn.execute('select report_key,item_count from email_report_active where singleton=1').fetchone()
if active:
    rows = conn.execute('select ref_num,message_id,created_at from max_email_report_refs where report_key=? order by ref_num', (active[0],)).fetchall()
    out['active_snapshot'] = {'expected_items':active[1], 'actual_items':len(rows),
        'count_matches':len(rows)==active[1], 'contiguous_ordinals':[r[0] for r in rows]==list(range(1,len(rows)+1)),
        'nonempty_unique_message_ids':all(r[1] for r in rows) and len({r[1] for r in rows})==len(rows),
        'created_at_min':min((r[2] for r in rows),default=None), 'created_at_max':max((r[2] for r in rows),default=None)}
out['latest_autonomy_action_at'] = conn.execute('select max(created_at) from email_autonomy_actions').fetchone()[0]
out['sensitive_values_exported'] = False
conn.close()
print(json.dumps(out))
