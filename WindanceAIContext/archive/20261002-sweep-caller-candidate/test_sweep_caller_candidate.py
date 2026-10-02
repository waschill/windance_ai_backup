"""Actual staged functions, synthetic main cases and loopback transport only."""
import ast,contextlib,http.server,io,json,os,threading,urllib.request
from pathlib import Path
s=Path('sweep-caller-private/candidate.private.py').read_text(encoding='utf-8');t=ast.parse(s)
env={'json':json,'urllib':__import__('urllib'),'HARNESS_SWEEP_URL':'fixture-sweep','NODE_RED_SEND_URL':'fixture-notice','PHONE':'fixture-recipient'}
nodes=[n for n in t.body if getattr(n,'name','') in {'main','post_json'}]
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<candidate>','exec'),env)
transport=env['post_json'];empty={'rules':0,'checked':0,'deleted':0,'kept':0,'notices':[],'errors':[]}
cases=[('empty',{},1),('valid_empty',empty,0),('boolean_count',dict(empty,checked=True),1),
       ('bad_count',dict(empty,deleted=1),1),('held',dict(empty,status='held'),1),
       ('error',dict(empty,errors=['PRIVATE_SENTINEL']),1),
       ('notice',dict(empty,notices=['PRIVATE_SENTINEL action outcome unconfirmed']),1)]
results=[]
for name,result,expected in cases:
 calls=[]
 def fake(url,payload,timeout):
  calls.append((url,payload,timeout));return result if url=='fixture-sweep' else {'ok':False,'delivered':False}
 env['post_json']=fake;buf=io.StringIO()
 with contextlib.redirect_stdout(buf):status=env['main']()
 assert status==expected and 'PRIVATE_SENTINEL' not in buf.getvalue()
 assert calls[0][2]==150
 if name=='notice':
  assert len(calls)==2 and 'auto-delete notice' not in calls[-1][1]['message']
  assert json.loads(buf.getvalue())['status']=='notification_unconfirmed'
 else:assert len(calls)==1
 results.append({'case':name,'exit':status})
def failed(*a,**k):raise TimeoutError('PRIVATE_SENTINEL')
env['post_json']=failed;buf=io.StringIO()
with contextlib.redirect_stdout(buf):assert env['main']()==1
assert 'PRIVATE_SENTINEL' not in buf.getvalue() and not json.loads(buf.getvalue())['retry_safe']
requests=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  self.rfile.read(int(self.headers.get('Content-Length',0)))
  requests.append((self.path,self.headers.get('Authorization')))
  if self.path=='/redirect':
   self.send_response(307);self.send_header('Location','/target');self.end_headers();return
  raw=json.dumps(empty).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
saved=os.environ.get('AGENT_HARNESS_TOKEN');os.environ.pop('AGENT_HARNESS_TOKEN',None)
try:
 base='http://127.0.0.1:'+str(server.server_port);env['HARNESS_SWEEP_URL']=base+'/sweep'
 try:transport(env['HARNESS_SWEEP_URL'],{},2);raise AssertionError('Missing auth accepted')
 except RuntimeError:pass
 assert not requests
 os.environ['AGENT_HARNESS_TOKEN']='synthetic-fixture'
 assert transport(env['HARNESS_SWEEP_URL'],{},2)==empty
 assert requests==[('/sweep','Bearer synthetic-fixture')]
 assert transport(base+'/notice',{},2)==empty and requests[-1]==('/notice',None)
 env['HARNESS_SWEEP_URL']=base+'/redirect'
 try:transport(env['HARNESS_SWEEP_URL'],{},2);raise AssertionError('Redirect accepted')
 except urllib.error.HTTPError as exc:assert exc.code==307
 assert len(requests)==3 and not any(p=='/target' for p,h in requests)
finally:
 if saved is None:os.environ.pop('AGENT_HARNESS_TOKEN',None)
 else:os.environ['AGENT_HARNESS_TOKEN']=saved
 server.shutdown();server.server_close();thread.join(2);assert not thread.is_alive()
print(json.dumps({'main_cases':results,'timeout_uncertainty_preserved':True,'private_error_contents_excluded':True,
 'missing_auth_zero_requests':True,'auth_only_to_sweep':True,'redirect_not_followed':True,'loopback_posts':len(requests),'real_endpoint_calls':0}))
