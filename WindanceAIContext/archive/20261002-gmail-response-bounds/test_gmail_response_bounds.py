"""Loopback compressed/slow response rejection through actual staged transport."""
import gzip,http.server,json,threading,time
from google.oauth2.credentials import Credentials
from gmail_single_attempt_transport import GmailTransport,TransportUnconfirmed
results=[]
for mode in ('gzip_ok','gzip_expansion','raw_oversize','truncated_gzip','gzip_trailing','slow_trickle'):
    attempts=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length','0')));attempts.append(1)
            payload=b'{"id":"fixture"}'
            zipped=mode.startswith('gzip') or mode=='truncated_gzip'
            if mode=='gzip_expansion':payload=b'x'*1000000
            if mode=='raw_oversize':payload=b'x'*2048
            if zipped:payload=gzip.compress(payload)
            if mode=='truncated_gzip':payload=payload[:-5]
            if mode=='gzip_trailing':payload+=b'trailing'
            self.send_response(200);self.send_header('Content-Length',str(len(payload)))
            if zipped:self.send_header('Content-Encoding','gzip')
            self.end_headers()
            try:
                if mode=='slow_trickle':
                    for value in payload:self.wfile.write(bytes([value]));self.wfile.flush();time.sleep(.04)
                else:self.wfile.write(payload)
            except (BrokenPipeError,ConnectionResetError):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
    transport=GmailTransport(Credentials(token='synthetic'),allow_loopback=True,read_timeout=.1,response_limit=1024,exchange_timeout=.15)
    start=time.monotonic();rejected=False
    try:
        try:
            response,body=transport.request(f'http://127.0.0.1:{server.server_port}/fixture',method='POST',body=b'{}')
            assert mode=='gzip_ok' and json.loads(body)=={'id':'fixture'}
            assert 'content-encoding' not in response and int(response['content-length'])==len(body)
        except TransportUnconfirmed:rejected=True;assert mode!='gzip_ok'
        elapsed=time.monotonic()-start
        assert len(attempts)==1
        if mode=='slow_trickle':assert elapsed<.4
        results.append({'scenario':mode,'rejected':rejected,'post_attempts':1,'elapsed_seconds':round(elapsed,3)})
    finally:transport.close();server.shutdown();server.server_close();thread.join(2);assert not thread.is_alive()
print(json.dumps({'cases':results,'real_google_calls':0,'limits':'Cooperative per-exchange deadline checked between raw chunks; not a hard whole-job/DNS/credential/lock deadline.'}))
