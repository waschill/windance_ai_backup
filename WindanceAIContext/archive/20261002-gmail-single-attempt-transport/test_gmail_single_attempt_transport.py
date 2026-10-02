"""Actual google client, HTTPX and loopback failures; no real Google credential."""
import http.server,json,socket,threading,time
from google.oauth2.credentials import Credentials
from googleapiclient.http import HttpRequest
from gmail_single_attempt_transport import GmailTransport
results=[]
for mode in ('normal','drop','malformed','timeout','redirect','unauthorized','server_error'):
    attempts=[];targets=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length','0')))
            attempts.append(1)
            if mode=='drop':self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
            if mode=='malformed':self.connection.sendall(b'NOT_HTTP\r\n\r\n');self.close_connection=True;return
            if mode=='timeout':time.sleep(.35);self.close_connection=True;return
            if mode=='redirect':
                self.send_response(307);self.send_header('Location','/redirect-target');self.end_headers();return
            code=401 if mode=='unauthorized' else 503 if mode=='server_error' else 200
            payload=b'{"id":"synthetic"}' if code==200 else b'{"error":"PRIVATE_SENTINEL"}'
            self.send_response(code);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.02),daemon=True);thread.start()
    transport=GmailTransport(Credentials(token='synthetic-fixture-token'),allow_loopback=True,read_timeout=.15)
    start=time.monotonic();error=None
    try:
        request=HttpRequest(transport,lambda response,content:json.loads(content),uri=f'http://127.0.0.1:{server.server_port}/synthetic-write',method='POST',body='{}')
        try:result=request.execute(num_retries=0)
        except Exception as exc:error=type(exc).__name__;assert 'PRIVATE_SENTINEL' not in str(exc)
        assert len(attempts)==1,(mode,attempts)
        assert (error is None)==(mode=='normal')
        if mode=='normal':assert result=={'id':'synthetic'}
    finally:
        transport.close();server.shutdown();server.server_close();thread.join(2);assert not thread.is_alive()
    results.append({'scenario':mode,'server_write_attempts':len(attempts),'error_type':error,'elapsed_seconds':round(time.monotonic()-start,3)})
# Refuse a non-provider target before credential preparation or network.
class NeverCredentials:
    def before_request(self,*args):raise AssertionError('Credential use before destination guard')
t=GmailTransport(NeverCredentials())
try:
    try:t.request('https://fixture.invalid/write',method='POST');raise AssertionError('Destination accepted')
    except RuntimeError as exc:assert 'destination refused' in str(exc)
finally:t.close()
print(json.dumps({'cases':results,'destination_guard':True,'real_google_calls':0,'production_changes':False,'limits':'Loopback HTTP; no production TLS, refresh-token exchange, full Harness integration or hard job deadline.'}))
