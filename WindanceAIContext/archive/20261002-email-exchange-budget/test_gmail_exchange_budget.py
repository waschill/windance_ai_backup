"""Actual local HTTP transport counts OAuth, errors and multiple instances."""
import http.server,json,sys,threading
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1]).resolve()))
from gmail_exchange_budget import exchange_budget,BudgetExhausted,charge_exchange
from gmail_single_attempt_transport import GmailTransport
calls=[]
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        calls.append(self.path);payload=b'{}'
        self.send_response(503 if self.path=='/error' else 200)
        self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
url='http://127.0.0.1:'+str(server.server_port)
class Credentials:
    def before_request(self,refresh,*args):refresh(url+'/oauth')
class PlainCredentials:
    def before_request(self,*args):pass
try:
    with exchange_budget(3) as budget:
        GmailTransport(Credentials(),allow_loopback=True).request(url+'/api')
        GmailTransport(PlainCredentials(),allow_loopback=True).request(url+'/error')
        assert calls==['/oauth','/api','/error'] and budget.used==3
        try:GmailTransport(PlainCredentials(),allow_loopback=True).request(url+'/refused')
        except BudgetExhausted:pass
        else:raise AssertionError('budget bypass')
        assert len(calls)==3
        try:
            with exchange_budget(2):pass
        except ValueError:pass
        else:raise AssertionError('nested reset')
    with exchange_budget(1) as budget:
        GmailTransport(PlainCredentials(),allow_loopback=True).request(url+'/next-operation')
        assert budget.used==1
    with exchange_budget(7) as budget:
        outcomes=[]
        def concurrent_charge():
            try:charge_exchange();outcomes.append('charged')
            except BudgetExhausted:outcomes.append('held')
        workers=[threading.Thread(target=concurrent_charge) for _ in range(20)]
        for worker in workers:worker.start()
        for worker in workers:worker.join()
        assert outcomes.count('charged')==7 and outcomes.count('held')==13 and budget.used==7
finally:server.shutdown();server.server_close();thread.join(2)
print(json.dumps({'status':'passed','oauth_and_error_counted':True,'multiple_transports_share_budget':True,'exhausted_no_network':True,'nested_reset_refused':True,'new_operation_independent':True,'thread_counter_atomic':True,'real_provider_calls':0}))
