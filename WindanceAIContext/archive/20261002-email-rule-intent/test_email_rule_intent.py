"""Actual schema/rules/report; synthetic accepted Trash with lost response."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(root/'agent_harness.candidate.private.py').read_text()
names={'db','ClosingConnection','seed_memories','gmail_autonomy_report','apply_email_sender_rules'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==5
fixed='email-rule-intent-' in str(root)
with tempfile.TemporaryDirectory() as folder:
 calls=[];effects=[];audits=[]
 item={'id':'fixture-message','from':'fixture@example.invalid','subject':'Synthetic','thread_id':'fixture-thread'}
 def trash(*args):
  effects.append('trash');raise TimeoutError('PRIVATE_ERROR_SENTINEL')
 def classify(items):calls.append(len(items));return {}
 def forbidden(*args,**kw):raise AssertionError('Unexpected action')
 ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':Path(folder)/'fixture.db','ensure_dirs':lambda:None,'dt':dt,'uuid':uuid,'re':re,'now':lambda:'fixture',
 'require_william_mailbox':lambda:None,'gmail_delete_message':trash,'gmail_create_draft':forbidden,
 'recent_inbox_email':lambda **k:[dict(item)],'save_email_report_refs':lambda *a,**kw:None,'classify_email_autonomy':classify,
 'email_autonomy_risk_reason':lambda x:None,'short_sender':lambda x:'fixture','compact_subject':lambda *a:'Synthetic',
 'sender_address':lambda x:'fixture@example.invalid','compose_numbered_email_draft':forbidden,'audit':lambda *a:audits.append(a),
 'email_sender_rules':lambda:{'fixture@example.invalid':{'action':'always_delete'}},'note_sender_rule_match':lambda *a:None,'gmail_state':lambda x:'inbox','email_importance':lambda x:'normal'}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-rules-report>','exec'),ns)
 report=ns['gmail_autonomy_report']()[0]
 # A separate sweep/direct rule application must also respect the durable hold.
 ns['apply_email_sender_rules']([dict(item)])
 if fixed:
  assert effects==['trash'] and calls==[]
  assert '1 previously attempted mailbox operation(s) remain unconfirmed' in report
  assert 'PRIVATE_ERROR_SENTINEL' not in report+repr(audits)
  with ns['db']() as c:assert c.execute("SELECT COUNT(*) FROM email_action_intents WHERE state='unconfirmed'").fetchone()[0]==1
 else:
  assert effects==['trash','trash'] and calls==[1]
 with ns['db']() as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 print(json.dumps({'fixed':fixed,'synthetic_trash_attempts':len(effects),'classifier_calls':len(calls),'actual_gmail_calls':0,'production_changes':False,'candidate_sha256':manifest['agent_harness.candidate.private.py']}))
