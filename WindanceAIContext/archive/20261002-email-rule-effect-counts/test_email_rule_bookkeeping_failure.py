"""Complete report/SDK/transport/journal in a worker, using a local Gmail fixture only."""
import base64,http.server,json,os,socket,sqlite3,sys,tempfile,threading
from contextlib import closing
from pathlib import Path
stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
from email_process_deadline import run
results=[]
for mode in ('normal',):
 with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);data=root/'data';data.mkdir();calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,value):
            payload=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
        def do_GET(self):
            calls.append(('GET',self.path.split('?')[0]))
            if self.path.split('?')[0].endswith('/profile'):
                self.reply({'emailAddress':'other@example.invalid' if mode=='wrong_account' else 'owner@example.invalid'});return
            if self.path.split('?')[0].endswith('/messages'):self.reply({'messages':[{'id':'fixture-message'}]});return
            self.reply({'id':'fixture-message','threadId':'fixture-thread','labelIds':['INBOX','UNREAD'],
                'snippet':'Synthetic newsletter','payload':{'mimeType':'text/plain','headers':[
                {'name':'From','value':'Fixture <fixture@example.invalid>'},{'name':'To','value':'owner@example.invalid'},
                {'name':'Subject','value':'Routine synthetic newsletter'}],
                'body':{'data':base64.urlsafe_b64encode(b'Synthetic newsletter').decode()}}})
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length',0)));path=self.path.split('?')[0];calls.append(('POST',path))
            assert path.endswith(('/modify','/trash'))
            if (mode=='lost_mark_read' and path.endswith('/modify')) or (mode=='lost_trash' and path.endswith('/trash')):
                self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            self.reply({'id':'fixture-message','labelIds':['TRASH'] if path.endswith('/trash') else ['INBOX']})
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
    worker=root/'fixture.py'
    worker.write_text('''import json,os,sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,STAGE)
import email_fixed_worker as fixed
def run(payload):
 scratch=Path(SCRATCH)
 for name in ['DATA','CONFIG','LOG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=str(scratch)
 os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=str(scratch)
 def guard(event,args):
  if event=='socket.connect' and args[1] not in [('127.0.0.1',PORT)]:raise RuntimeError('Non-fixture connection forbidden')
 sys.addaudithook(guard)
 def loader():
  h=fixed.load_harness();h.startup()
  marker=scratch/'bookkeeping-failure-once'
  if not marker.exists():
   import sqlite3
   actual_db=h.db
   def guarded_db():
    c=actual_db()
    c.set_authorizer(lambda action,arg1,arg2,db,trigger:sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_INSERT and arg1=='email_sender_rule_receipts' else sqlite3.SQLITE_OK)
    return c
   h.db=guarded_db
   marker.write_text('fixture')
  assert h.GOOGLE_TOKEN_FILE.resolve().is_relative_to(scratch.resolve())
  h.GOOGLE_TOKEN_FILE.parent.mkdir(parents=True,exist_ok=True)
  h.GOOGLE_TOKEN_FILE.write_text(json.dumps({'token':'synthetic','refresh_token':'fixture','client_id':'fixture','client_secret':'fixture','expiry':'2099-01-01T00:00:00Z'}))
  if MODE!='missing_policy':(h.GOOGLE_TOKEN_FILE.parent/'gmail-account-policy.json').write_text(json.dumps({'expected_email':'owner@example.invalid'}))
  import gmail_single_attempt_transport as transport
  original=transport.GmailTransport
  class LocalTransport(original):
   def __init__(self,creds):super().__init__(creds,allow_loopback=True,read_timeout=.5)
   def request(self,uri,*a,**k):
    parsed=urlsplit(uri);assert parsed.hostname=='gmail.googleapis.com'
    return super().request('http://127.0.0.1:PORT'+parsed.path+('?' + parsed.query if parsed.query else ''),*a,**k)
  transport.GmailTransport=LocalTransport
  def model(*a,**k):return json.dumps([{'index':1,'decision':'automatic','category':'newsletter','reason':'Synthetic fixture','draft_intent':''}]),'fixture','fixture'
  h.model_reply=lambda *a,**k: (_ for _ in ()).throw(AssertionError('Model forbidden'))
  h.upsert_email_sender_rule('always_delete', {'sender':'fixture@example.invalid','message_id':'fixture-message','subject':'Synthetic'})
  def forbidden(*a,**k):raise AssertionError('Dispatch forbidden')
  h.dispatch_staff_worker=forbidden
  return h
 return fixed.execute(payload,loader=loader)
'''.replace('STAGE',repr(str(stage))).replace('SCRATCH',repr(str(data))).replace('PORT',str(server.server_port)).replace('MODE',repr(mode)))
    try:
        first=run(worker,{'owner':'william','operation':'sender_rule_sweep','limit':25},timeout=30)
        writes=[p for method,p in calls if method=='POST'];assert len(writes)==2
        assert first['deleted']==0 and first['kept']==1
        with closing(sqlite3.connect(data/'harness.db')) as c:
            assert c.execute('SELECT state FROM email_action_intents').fetchall()==[('confirmed',)]
            assert c.execute('SELECT sum(match_count) FROM max_email_sender_rules').fetchone()[0]==0
            assert c.execute('SELECT count(*) FROM email_sender_rule_receipts').fetchone()[0]==0
        second=run(worker,{'owner':'william','operation':'sender_rule_sweep','limit':25},timeout=30)
        assert second['effects']=={'newly_confirmed':0,'previously_confirmed':1}
        assert [p for method,p in calls if method=='POST']==writes
        with closing(sqlite3.connect(data/'harness.db')) as c:
            assert c.execute('SELECT sum(match_count) FROM max_email_sender_rules').fetchone()[0]==1
        results.append({'mode':'bookkeeping_write_failure','confirmed_effect_preserved':True,'repair_on_relisted_message':True,'no_repeat_write':True,'unlisted_message_recovery_unproven':True})
    finally:server.shutdown();server.server_close();thread.join(2);assert not thread.is_alive()
print(json.dumps({'cases':results,'actual_sweep_sdk_cache_transport_journal':True,
    'real_provider_or_model_calls':0,'limits':'Local HTTP fixture; model calls forbidden; real identity/TLS/provider delivery, installed API/scheduler and full recovery remain unverified.'}))
