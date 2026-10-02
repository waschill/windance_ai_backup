"""Actual approve_pending under overlapping snapshot and uncertain callback."""
import ast,json,sqlite3,sys,tempfile,threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
root=Path(sys.argv[1]);s=(root/'agent_harness.candidate.private.py').read_text()
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='approve_pending')
fixed='email-approval-claim-' in str(root);results=[]
class Connection(sqlite3.Connection):
 def __exit__(self,*args):
  try:return super().__exit__(*args)
  finally:self.close()
for mode in ['overlap','lost_response']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db';calls=[];barrier=threading.Barrier(2)
  def db():
   c=sqlite3.connect(path,timeout=5,factory=Connection);c.row_factory=sqlite3.Row;return c
  with db() as c:
   c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)')
   c.execute("INSERT INTO approvals VALUES('fixture-approval','gmail.delete','{}','pending','fixture-time',NULL,NULL)")
  def find(short_id):
   with db() as c:r=c.execute("SELECT * FROM approvals WHERE status='pending'").fetchone()
   if mode=='overlap':barrier.wait(timeout=5)
   return dict(r) if r else None
  def execute(*args):
   calls.append('effect')
   if mode=='lost_response':raise TimeoutError('PRIVATE_SENTINEL')
   return {'ok':True}
  ns={'require_william_mailbox':lambda:None,'find_pending_approval':find,'approval_is_fresh':lambda a:True,'json':json,'db':db,'now':lambda:'fixture-time','audit':lambda *a:None,'execute_approved_action':execute}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-approval>','exec'),ns)
  if mode=='overlap':
   with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:ns['approve_pending']('fixture'),range(2)))
   assert len(calls)==(1 if fixed else 2)
  else:
   responses=[ns['approve_pending']('fixture')]
   if fixed:assert 'PRIVATE_SENTINEL' not in repr(responses)
  with db() as c:state=c.execute('SELECT status FROM approvals').fetchone()[0]
  assert state==('executed' if mode=='overlap' else ('uncertain' if fixed else 'failed'))
  results.append({'case':mode,'synthetic_effects':len(calls),'status':state})
print(json.dumps({'fixed':fixed,'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Concurrent threads and synthetic callbacks; process-death, selected-number approvals, batch item recovery and status consumers not covered.'}))
