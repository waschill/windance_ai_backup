"""Actual report with simulated remote acceptance followed by lost response."""
import ast,datetime as dt,hashlib,json,re,sqlite3,sys,tempfile,uuid
from pathlib import Path
from typing import Any
paths={'baseline':Path('/Users/herald/services/agent-harness/agent_harness.py'),'candidate':Path('/Users/herald/backups/email-outcome-candidate-20261002/agent_harness.candidate.private.py')}
if len(sys.argv)>1:
 paths['candidate']=Path(sys.argv[1]);sys.path.insert(0,str(paths['candidate'].parent))
 from email_action_intent import install
outcomes=[]
for version,path in paths.items():
 node=next(n for n in ast.parse(path.read_text()).body if getattr(n,'name','')=='gmail_autonomy_report')
 for mode in ['trash_ok','trash_lost','draft_ok','draft_lost','draft_empty_receipt','prepare_error']:
  with tempfile.TemporaryDirectory(prefix='email-outcome-') as directory:
   database=Path(directory)/'fixture.db';effects=[];attempts=[]
   def db():
    c=sqlite3.connect(database);c.row_factory=sqlite3.Row;return c
   with db() as c:c.execute('CREATE TABLE email_autonomy_actions(run_id TEXT,ordinal INTEGER,message_id TEXT,thread_id TEXT,sender TEXT,subject TEXT,decision TEXT,action TEXT,reason TEXT,draft_id TEXT,created_at TEXT)')
   if len(sys.argv)>1:
    with db() as c:install(c)
   def compose(*args):
    if mode=='prepare_error':raise RuntimeError('synthetic private exception marker')
    return 'synthetic unsent body'
   def effect(*args):
    attempts.append(1);effects.append('trash' if mode.startswith('trash') else 'draft')
    if mode.endswith('lost'):raise TimeoutError('synthetic private exception marker')
    if mode=='draft_empty_receipt':return {'draft_created':True,'id':''}
    return {'trashed':True,'id':'fixture-message'} if mode.startswith('trash') else {'draft_created':True,'id':'fixture-draft'}
   item={'id':'fixture-message','thread_id':'fixture-thread','from':'fixture@example.invalid','subject':'synthetic'}
   ns={'Any':Any,'dt':dt,'uuid':uuid,'re':re,'db':db,'now':lambda:'fixture-time','require_william_mailbox':lambda:None,
       'recent_inbox_email':lambda **k:[item],'apply_email_sender_rules':lambda items:(items,[]),
       'save_email_report_refs':lambda *a,**k:None,'classify_email_autonomy':lambda x:{1:{'decision':'automatic' if mode.startswith('trash') else 'draft','reason':'fixture','draft_intent':'fixture'}},
       'email_autonomy_risk_reason':lambda x:None,'short_sender':lambda x:'fixture','compact_subject':lambda *a:'synthetic',
       'sender_address':lambda x:'fixture@example.invalid','compose_numbered_email_draft':compose,'gmail_create_draft':effect,'gmail_delete_message':effect,'audit':lambda *a:None}
   exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-report>','exec'),ns);report=ns['gmail_autonomy_report']()[0]
   with db() as c:row=dict(c.execute('SELECT action,reason,draft_id FROM email_autonomy_actions').fetchone())
   if version=='candidate':
    expected={'trash_ok':'trashed','draft_ok':'draft_created','prepare_error':'error_before_action'}.get(mode,'action_outcome_unknown')
    assert row['action']==expected and 'synthetic private exception marker' not in report
    assert 'Escalated messages were not changed.' not in report
    if expected=='action_outcome_unknown':assert 'outcome unconfirmed' in report
   elif mode.endswith('lost'):assert row['action']=='error_left_untouched' and effects
   outcomes.append({'version':version,'case':mode,'simulated_accepted_effects':len(effects),'recorded_action':row['action'],'actual_mailbox_actions':0})
print(json.dumps({'candidate_sha256':hashlib.sha256(paths['candidate'].read_bytes()).hexdigest(),'cases':outcomes,'actual_model_calls':0,'production_changes':False,'limits':'Truthful outcome reporting only; durable pre-action intents, concurrent claims and authoritative Gmail reconciliation remain open'}))
