"""Full private module, fixed worker routing and real subprocess; external effects denied."""
import json,os,shutil,sys,tempfile
from pathlib import Path
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
import email_fixed_worker as fixed
from email_process_deadline import run
invalid=[{'owner':owner,'operation':'report','limit':25} for owner in ('shawn',None,'','William')]
invalid += [{'owner':'william','operation':op,'limit':25} for op in ('send','arbitrary','__import__')]
invalid += [{'owner':'william','operation':'report','limit':limit} for limit in (0,51,True,'25')]
invalid += [{'owner':'william','operation':'report','limit':25,'path':'elsewhere'}]
def forbidden():raise AssertionError('Rejected input reached loader')
for payload in invalid:
    try:fixed.execute(payload,loader=forbidden);raise AssertionError('Invalid input accepted')
    except (ValueError,PermissionError):pass
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);worker=root/'fixture_worker.py'
    worker.write_text('''import os,sys,json
from pathlib import Path
sys.path.insert(0,STAGE)
import email_fixed_worker as fixed
def run(payload):
 scratch=Path(SCRATCH)
 for name in ['DATA','CONFIG','LOG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
 os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch)
 def guard(event,args):
  if event=='socket.connect':raise RuntimeError('External connection forbidden')
 sys.addaudithook(guard)
 def loader():
  h=fixed.load_harness()
  h.audit=lambda event,data:(scratch/'audit.json').write_text(json.dumps([event,data]))
  h.startup()
  def no_effect(*a,**k):raise AssertionError('Remote/model effect forbidden')
  h.model_reply=no_effect;h.dispatch_staff_worker=no_effect
  def inbox(*a,**k):
   import email_owner_boundary
   assert email_owner_boundary._owner.get()=='william'
   if payload['limit']==1:raise RuntimeError('PRIVATE_SENTINEL')
   return []
  h.recent_inbox_email=inbox
  h.email_sender_rules=lambda:{}
  h.gmail_service=no_effect
  return h
 return fixed.execute(payload,loader=loader)
'''.replace('STAGE',repr(str(stage))).replace('SCRATCH',repr(str(root/'data'))))
    response=run(worker,{'owner':'william','operation':'report','limit':25},timeout=10)
    assert response['model']=='gmail-autonomy' and 'No new inbox messages' in response['reply'],response['model']
    failed=run(worker,{'owner':'william','operation':'report','limit':1},timeout=10)
    assert failed['model']=='gmail-error'
    assert 'PRIVATE_SENTINEL' not in json.dumps(failed)+(root/'data/audit.json').read_text()
    # Content tampering is rejected before execution/import.
    changed=root/'changed';shutil.copytree(stage,changed)
    with (changed/'email_classification_contract.py').open('a') as stream:stream.write('\n# changed fixture\n')
    fixed.ROOT=changed.resolve()
    try:fixed.load_harness();raise AssertionError('Altered source accepted')
    except RuntimeError as exc:assert str(exc)=='Worker package changed'
    finally:fixed.ROOT=stage
print(json.dumps({'invalid_payloads_rejected_before_load':len(invalid),'full_harness_import':True,
    'actual_empty_inbox_report_in_subprocess':True,'failed_report_and_audit_sanitized':True,'owner_context_forwarded':True,'source_tamper_rejected':True,
    'real_provider_calls':0,'limits':'Fixtures replace mailbox reads and audit; no real request authentication, nonempty report, model, scheduler or production deployment.'}))
