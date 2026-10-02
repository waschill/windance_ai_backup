"""Actual candidate DB/seed/connection/report functions; isolated effect failures."""
import ast,datetime as dt,hashlib,json,os,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-intent-visibility-20261002');sys.path.insert(0,str(root))
source=(root/'agent_harness.candidate.private.py').read_text()
names={'db','ClosingConnection','seed_memories','gmail_autonomy_report'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==4
results=[]
for mode in ['unknown_missing_inbox','confirmed_receipt_failure','unknown_still_inbox']:
 with tempfile.TemporaryDirectory(prefix='email-visibility-') as directory:
  folder=Path(directory);calls=[];effects=[];rules=[];inbox=[{'id':'fixture-message','thread_id':'fixture-thread','from':'fixture@example.invalid','subject':'synthetic'}]
  def classify(items):calls.append('classify');return {1:{'decision':'draft','reason':'fixture','draft_intent':'fixture'}}
  def compose(*a):calls.append('compose');return 'synthetic body'
  def create(*a):
   effects.append('draft')
   if mode.startswith('unknown'):raise TimeoutError('fixture accepted but lost acknowledgment')
   return {'draft_created':True,'id':'fixture-draft'}
  def apply_rules(items):rules.append(len(items));return items,[]
  ns={'Any':Any,'sqlite3':sqlite3,'os':os,'DB_FILE':folder/'fixture.db','ensure_dirs':lambda:None,
      'dt':dt,'uuid':uuid,'re':re,'now':lambda:'fixture-time','require_william_mailbox':lambda:None,
      'recent_inbox_email':lambda **k:list(inbox),'apply_email_sender_rules':apply_rules,
      'save_email_report_refs':lambda *a,**k:None,'classify_email_autonomy':classify,
      'email_autonomy_risk_reason':lambda x:None,'short_sender':lambda x:'fixture','compact_subject':lambda *a:'synthetic',
      'sender_address':lambda x:'fixture@example.invalid','compose_numbered_email_draft':compose,'gmail_create_draft':create,
      'gmail_delete_message':lambda *a:(_ for _ in ()).throw(AssertionError('Unexpected Trash')),'audit':lambda *a:None}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-candidate-db-report>','exec'),ns)
  with ns['db']() as c:
   if mode=='confirmed_receipt_failure':c.execute("CREATE TRIGGER fail_action_receipt BEFORE INSERT ON email_autonomy_actions BEGIN SELECT RAISE(ABORT,'fixture insert failure'); END")
  try:ns['gmail_autonomy_report']()
  except sqlite3.IntegrityError:assert mode=='confirmed_receipt_failure'
  if mode=='unknown_missing_inbox':inbox.clear()
  if mode=='confirmed_receipt_failure':
   with ns['db']() as c:c.execute('DROP TRIGGER fail_action_receipt')
  report=ns['gmail_autonomy_report']()[0]
  assert calls==['classify','compose'] and effects==['draft'] and rules==[1,0]
  if mode.startswith('unknown'):assert '1 previously attempted mailbox operation(s) remain unconfirmed' in report
  else:assert 'already have durable action records' in report
  with ns['db']() as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  results.append({'case':mode,'synthetic_effects':len(effects),'total_classifier_calls':calls.count('classify'),'total_composition_calls':calls.count('compose'),'second_rule_input_items':rules[-1],'held_or_recorded_status_visible':True})
print(json.dumps({'candidate_sha256':hashlib.sha256((root/'agent_harness.candidate.private.py').read_bytes()).hexdigest(),'cases':results,'actual_candidate_db_schema':True,'actual_mailbox_calls':0,'actual_model_calls':0,'production_changes':False,'limits':'No full app HTTP startup, live data migration, authoritative reconciliation or legacy action-row repair'}))
