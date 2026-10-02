"""Actual legacy context functions with disposable synthetic DB and no network."""
import ast,hashlib,json,pathlib,re,sqlite3,sys,tempfile,urllib.request
p=pathlib.Path.home()/'services/desktop-context-sync/desktop_context_sync.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b4654e49d7a1592c4aa41d043bfe2e5f367ce03b9b4fd5b6f9af4df30a62d974'
t=ast.parse(raw);nodes=[n for n in t.body if getattr(n,'name','') in ('clean','latest_context','publish')]
def guard(event,args):
 if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:raise RuntimeError('External effects denied')
sys.addaudithook(guard)
with tempfile.TemporaryDirectory() as tmp:
 db=pathlib.Path(tmp)/'synthetic.db';c=sqlite3.connect(db)
 c.executescript('CREATE TABLE sessions(id TEXT,title TEXT,started_at TEXT,source TEXT);CREATE TABLE messages(session_id TEXT,role TEXT,content TEXT,timestamp TEXT);')
 c.execute('INSERT INTO sessions VALUES(?,?,?,?)',('synthetic','Synthetic private conversation','2026-10-02','desktop'))
 c.execute('INSERT INTO messages VALUES(?,?,?,?)',('synthetic','user','PRIVATE_CONTEXT_SENTINEL: a personal reflection, not a request to remember or share.','2026-10-02'));c.commit();c.close()
 env={'sqlite3':sqlite3,'re':re,'json':json,'urllib':__import__('urllib'),'STATE_DB':db,'HARNESS_URL':'http://fixture.invalid/not-called'}
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<actual-context-functions>','exec'),env)
 value=env['latest_context']();captured=[]
 class Response:
  def __enter__(self):return self
  def __exit__(self,*a):pass
  def read(self):return b'{}'
 def fake(request,timeout):captured.append(json.loads(request.data));return Response()
 original=urllib.request.urlopen;urllib.request.urlopen=fake
 try:env['publish'](value)
 finally:urllib.request.urlopen=original
 payload=captured[0]
 result={'source_sha256':hashlib.sha256(raw).hexdigest(),'synthetic_personal_excerpt_in_payload':'PRIVATE_CONTEXT_SENTINEL' in payload['value'],
         'explicit_remember_command_required':False,'payload_has_owner_field':'owner' in payload or 'user_id' in payload,
         'payload_has_session_id':any(k in payload for k in ('session_id','source_id')),
         'shared_kind':payload['kind'],'shared_key':payload['key'],'external_calls':0,'production_changes':False,
         'limit':'Demonstrates selected synthetic function path, not actual prior disclosure or every possible upstream identity check.'}
 assert result['synthetic_personal_excerpt_in_payload'] and not result['payload_has_owner_field']
 print(json.dumps(result))
