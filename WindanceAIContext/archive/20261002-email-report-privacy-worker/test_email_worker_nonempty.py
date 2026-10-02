"""Full staged report in a subprocess with synthetic mailbox/classifier effects."""
import json,sqlite3,sys,tempfile
from contextlib import closing
from pathlib import Path
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
from email_process_deadline import run,WorkerUnconfirmed
results=[]
for mode in ('confirmed','interrupted'):
 with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);worker=root/'fixture.py';data=root/'data';effects=root/'effects'
    worker.write_text('''import os,sys,time,json
from pathlib import Path
sys.path.insert(0,STAGE)
import email_fixed_worker as fixed
def run(payload):
 scratch=Path(SCRATCH)
 for name in ['DATA','CONFIG','LOG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
 os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch)
 def guard(event,args):
  if event=='socket.connect':raise RuntimeError('Real provider connection forbidden')
 sys.addaudithook(guard)
 def loader():
  h=fixed.load_harness();h.audit=lambda *a,**k:None;h.startup()
  def forbidden(*a,**k):raise AssertionError('Real model or dispatch forbidden')
  h.model_reply=forbidden;h.dispatch_staff_worker=forbidden;h.gmail_service=forbidden
  h.recent_inbox_email=lambda **k:[{'id':'fixture-message','thread_id':'fixture-thread','from':'Fixture <fixture@example.invalid>','subject':'Routine fixture newsletter','body':'Synthetic newsletter','snippet':'Synthetic','labels':['INBOX']}]
  h.email_sender_rules=lambda:{}
  h.classify_email_autonomy=lambda items:{1:{'decision':'automatic','category':'newsletter','reason':'Synthetic fixture decision','draft_intent':''}}
  def effect(message_id):
   with open(EFFECTS,'a') as stream:stream.write('one\\n')
   if payload['limit']==26:time.sleep(8)
   return {'trashed':True,'id':message_id}
  h.gmail_delete_message=effect
  return h
 return fixed.execute(payload,loader=loader)
'''.replace('STAGE',repr(str(stage))).replace('SCRATCH',repr(str(data))).replace('EFFECTS',repr(str(effects))))
    payload={'owner':'william','operation':'report','limit':26 if mode=='interrupted' else 25}
    if mode=='interrupted':
        try:run(worker,payload,timeout=2);raise AssertionError('Hung report succeeded')
        except WorkerUnconfirmed:pass
    else:
        response=run(worker,payload,timeout=5);assert response['model']=='gmail-autonomy-v1'
    assert effects.read_text().splitlines()==['one']
    db=data/'harness.db'
    with closing(sqlite3.connect(db)) as c:
        states=c.execute('SELECT state FROM email_action_intents').fetchall()
        assert states==[('unconfirmed' if mode=='interrupted' else 'confirmed',)]
    retry=run(worker,{'owner':'william','operation':'report','limit':25},timeout=5)
    assert effects.read_text().splitlines()==['one']
    if mode=='interrupted':assert retry['model']=='gmail-autonomy-held'
    results.append({'scenario':mode,'fixture_effect_count':1,'intent':states[0][0],'second_report_no_replay':True})
print(json.dumps({'cases':results,'full_candidate_report_functions':True,'real_provider_or_model_calls':0,
    'limits':'Synthetic inbox/classifier/provider primitive; no real authentication, transport, user acceptance or scheduler integration.'}))
