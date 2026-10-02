"""Actual report refuses new preparation when approved operation is uncertain."""
import ast,datetime as dt,hashlib,json,os,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-shared-harness-20261002');sys.path.insert(0,str(root))
from email_approved_item_intent import perform,ItemHeld
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text();names={'db','ClosingConnection','seed_memories','gmail_autonomy_report'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==4
with tempfile.TemporaryDirectory() as folder:
 calls=[]
 def forbidden(*a,**kw):calls.append('forbidden');raise AssertionError('Report must hold before preparation')
 ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'json':json,'now':lambda:'fixture','require_william_mailbox':lambda:None,'recent_inbox_email':forbidden,'classify_email_autonomy':forbidden,'apply_email_sender_rules':forbidden,'save_email_report_refs':forbidden}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-held-report>','exec'),ns)
 with ns['db']() as c:c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES('fixture','gmail.delete',?,'executing','fixture')",(json.dumps({'message_id':'fixture-message'}),))
 def lost(item):raise TimeoutError('synthetic accepted effect')
 try:perform(ns['db'],'fixture',0,lost,lambda i,r:r)
 except ItemHeld:pass
 response=ns['gmail_autonomy_report']()
 assert response[2]=='gmail-autonomy-held' and 'active or unconfirmed' in response[0] and not calls
 with ns['db']() as c:
  assert c.execute('SELECT COUNT(*) FROM email_mailbox_admission').fetchone()[0]==1
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'held_report_before_inbox_model_rules_or_snapshot':True,'reservation_preserved':True,'actual_mailbox_calls':0,'production_changes':False,'limits':'Synthetic existing approved hold; no operator resolution, actual sending, startup backfill or undo coverage.'}))
