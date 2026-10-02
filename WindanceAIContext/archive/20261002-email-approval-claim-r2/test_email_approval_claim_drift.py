"""Actual approval claim expiration and competing final-status modification."""
import ast,json,sqlite3,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]);s=(root/'agent_harness.candidate.private.py').read_text()
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='approve_pending')
fixed='claim-r2-' in str(root);results=[]
class Connection(sqlite3.Connection):
 def __exit__(self,*args):
  try:return super().__exit__(*args)
  finally:self.close()
for mode in ['expires_before_claim','final_status_changed']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db';calls=[];fresh=[]
  def db():
   c=sqlite3.connect(path,factory=Connection);c.row_factory=sqlite3.Row;return c
  with db() as c:
   c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)')
   c.execute("INSERT INTO approvals VALUES('fixture','gmail.delete','{}','pending','fixture',NULL,NULL)")
  def find(short_id):
   with db() as c:return dict(c.execute('SELECT * FROM approvals').fetchone())
  def is_fresh(a):fresh.append(1);return not(mode=='expires_before_claim' and len(fresh)>1)
  def execute(*args):
   calls.append('effect')
   if mode=='final_status_changed':
    with db() as c:c.execute("UPDATE approvals SET status='fixture_conflicting_state'")
   return {'ok':True}
  ns={'require_william_mailbox':lambda:None,'find_pending_approval':find,'approval_is_fresh':is_fresh,'json':json,'db':db,'now':lambda:'fixture','audit':lambda *a:None,'execute_approved_action':execute}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-approval-drift>','exec'),ns)
  response=None;error=None
  try:response=ns['approve_pending']('fixture')
  except RuntimeError as exc:error=str(exc)
  if fixed:
   if mode=='expires_before_claim':assert not calls and response[2]=='approval-expired'
   else:assert calls==['effect'] and response is None and 'status changed' in error
  else:assert calls==['effect'] and 'Approved and executed' in response[0]
  results.append({'case':mode,'synthetic_effects':len(calls),'false_success_prevented':fixed})
print(json.dumps({'fixed':fixed,'cases':results,'actual_mailbox_calls':0,'production_changes':False}))
