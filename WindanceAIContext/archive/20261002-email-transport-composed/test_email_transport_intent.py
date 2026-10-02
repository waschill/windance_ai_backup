"""Exact candidate functions + real durable journal + Google SDK + loopback HTTP."""
import ast,hashlib,http.server,json,socket,sqlite3,sys,tempfile,threading
from pathlib import Path
from contextlib import closing
from google.oauth2.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import build
stage=Path(sys.argv[1]);sys.path.insert(0,str(stage))
import gmail_single_attempt_transport as transport_module
from email_action_intent import install,perform_recoverable_draft,OutcomeHeld
manifest=json.loads((stage/'manifest.json').read_text())
assert all(hashlib.sha256((stage/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
source=(stage/'agent_harness.candidate.private.py').read_text(encoding='utf-8')
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in {'gmail_service','_gmail_create_prepared_draft'}]
assert len(nodes)==2
original_transport=transport_module.GmailTransport;results=[]
for mode in ('success','lost_response'):
    attempts=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length','0')));attempts.append(1)
            if mode=='lost_response':self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            payload=b'{"id":"synthetic-draft"}'
            self.send_response(200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.02),daemon=True);thread.start()
    class LoopbackTransport(original_transport):
        def __init__(self,creds):super().__init__(creds,allow_loopback=True,read_timeout=.25)
        def request(self,uri,*args,**kwargs):
            assert uri.startswith('https://gmail.googleapis.com/gmail/v1/')
            return super().request(f'http://127.0.0.1:{server.server_port}/synthetic-draft',*args,**kwargs)
    class Credentials:
        @staticmethod
        def from_authorized_user_file(*args):return GoogleCredentials(token='synthetic')
    transport_module.GmailTransport=LoopbackTransport
    namespace={'Any':object,'Credentials':Credentials,'GOOGLE_TOKEN_FILE':Path('unused-fixture'),
        'SCOPES':[],'require_william_mailbox':lambda:None,'build':build}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-candidate-functions>','exec'),namespace)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'fixture.db'
            def connect():return sqlite3.connect(db)
            with closing(connect()) as c:install(c)
            request={'to':'fixture@example.invalid','subject':'fixture','body':'fixture','thread_id':None}
            for attempt in range(2):
                try:
                    receipt=perform_recoverable_draft(connect,'william','synthetic-source',request,namespace['_gmail_create_prepared_draft'])
                    assert mode=='success' and receipt=={'draft_created':True,'id':'synthetic-draft'}
                except OutcomeHeld:assert mode=='lost_response'
                with closing(connect()) as c:
                    rows=c.execute('SELECT state FROM email_action_intents').fetchall()
                    assert rows==[('confirmed' if mode=='success' else 'unconfirmed',)]
                assert len(attempts)==1
                if attempt==0:
                    cold=Path(tmp)/'cold.db'
                    with closing(connect()) as c,closing(sqlite3.connect(cold)) as b:c.backup(b)
                    db=cold  # Retry through a restored database, not an in-memory cache.
            results.append({'scenario':mode,'remote_attempts':len(attempts),'cold_retry_no_replay':True,'state':rows[0][0]})
    finally:
        transport_module.GmailTransport=original_transport
        server.shutdown();server.server_close();thread.join(2);assert not thread.is_alive()
print(json.dumps({'candidate':manifest['agent_harness.candidate.private.py'],'cases':results,'real_google_calls':0,
    'limits':'Exact two functions and journal, synthetic credential/owner gate and loopback rewrite; no full service startup, account identity or production TLS proof.'}))
