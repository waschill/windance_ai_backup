"""Actual staged submit and urllib on loopback, with a synthetic service token."""
import ast,http.server,io,json,os,threading,urllib.request,urllib.error,re
from pathlib import Path
from types import SimpleNamespace
s=Path('gmail-caller-private/candidate.private.py').read_text(encoding='utf-8')
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='submit')
saved=os.environ.get('AGENT_HARNESS_TOKEN');results=[]
try:
 for mode in ('normal','failure503','redirect','legacy_error','missing'):
    attempts=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length',0)))
            attempts.append(self.headers.get('Authorization'))
            if mode=='redirect':
                self.send_response(307);self.send_header('Location','/redirect-target');self.end_headers();return
            payload=json.dumps({'reply':'synthetic','model':'gmail-error' if mode=='legacy_error' else 'gmail-autonomy'}).encode()
            self.send_response(503 if mode=='failure503' else 200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
    def request(url,*a,**k):
        assert url=='http://127.0.0.1:8791/gmail/report'
        return urllib.request.Request(f'http://127.0.0.1:{server.server_port}/fixture',*a,**k)
    proxy=SimpleNamespace(request=SimpleNamespace(Request=request,HTTPRedirectHandler=urllib.request.HTTPRedirectHandler,
        ProxyHandler=urllib.request.ProxyHandler,build_opener=urllib.request.build_opener),error=urllib.error)
    ns={'re':re,'json':json,'urllib':proxy};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-submit>','exec'),ns)
    os.environ['AGENT_HARNESS_TOKEN']='' if mode=='missing' else 'synthetic-fixture'
    try:
        try:
            result=ns['submit']('show email report');assert mode in ('normal','legacy_error')
            assert result['isError']==(mode=='legacy_error')
        except RuntimeError as e:
            assert mode in ('failure503','redirect','missing') and 'synthetic-fixture' not in str(e)
        assert attempts==([] if mode=='missing' else ['Bearer synthetic-fixture'])
        results.append({'mode':mode,'post_attempts':len(attempts)})
    finally:server.shutdown();server.server_close();thread.join(2);assert not thread.is_alive()
finally:
 if saved is None:os.environ.pop('AGENT_HARNESS_TOKEN',None)
 else:os.environ['AGENT_HARNESS_TOKEN']=saved
print(json.dumps({'cases':results,'authorization_header_verified':True,'redirect_not_followed':True,'real_service_calls':0,'live_config_changes':False}))
