"""Actual claim handler, real child termination, fresh-process and cold retry."""
import ast,hashlib,json,os,sqlite3,subprocess,sys,tempfile
from contextlib import closing
from pathlib import Path
from typing import Any
root=Path('/Users/herald/backups/email-approval-claim-r2-20261002')
source=root/'agent_harness.candidate.private.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='96ceb3e4abe378d4bcf3648d68e810044aabf79c16bbbe78b0a42d5411690892'
nodes=[n for n in ast.parse(source.read_text()).body if getattr(n,'name','') in {'approve_pending','find_pending_approval'}];assert len(nodes)==2
class Connection(sqlite3.Connection):
 def __exit__(self,*args):
  try:return super().__exit__(*args)
  finally:self.close()
def child(folder,mode):
 path=Path(folder)/'fixture.db';effect=Path(folder)/'effect.jsonl'
 def db():
  c=sqlite3.connect(path,factory=Connection);c.row_factory=sqlite3.Row;return c
 def execute(*args):
  if mode=='before_effect':os._exit(70)
  with effect.open('a') as f:f.write('"synthetic effect"\n');f.flush();os.fsync(f.fileno())
  if mode=='after_effect':os._exit(71)
  return {'ok':True}
 def audit(*args):
  if mode=='after_receipt':os._exit(72)
 ns={'Any':Any,'require_william_mailbox':lambda:None,'approval_is_fresh':lambda a:True,'json':json,'db':db,'now':lambda:'fixture','audit':audit,'execute_approved_action':execute}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-approval-recovery>','exec'),ns)
 ns['approve_pending']('fixture')
if len(sys.argv)>1:
 child(sys.argv[1],sys.argv[2]);sys.exit(0)
results=[]
for mode,exitcode in [('before_effect',70),('after_effect',71),('after_receipt',72)]:
 with tempfile.TemporaryDirectory() as directory:
  folder=Path(directory);path=folder/'fixture.db'
  with closing(sqlite3.connect(path)) as c:
   c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)')
   c.execute("INSERT INTO approvals VALUES('fixture-approval','gmail.delete','{}','pending','fixture',NULL,NULL)");c.commit()
  def run(where,step):return subprocess.run([sys.executable,__file__,str(where),step],timeout=15,capture_output=True)
  outcome=run(folder,mode)
  assert outcome.returncode==exitcode,(outcome.returncode,outcome.stderr.decode()[-1800:])
  effect=folder/'effect.jsonl';before=effect.read_bytes() if effect.exists() else b''
  assert len(before.splitlines())==(0 if mode=='before_effect' else 1)
  with closing(sqlite3.connect(path)) as c:
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
   state=c.execute('SELECT status FROM approvals').fetchone()[0]
   assert state==('executed' if mode=='after_receipt' else 'executing')
   cold=folder/'cold';cold.mkdir()
   with closing(sqlite3.connect(cold/'fixture.db')) as target:c.backup(target)
  assert run(folder,'retry').returncode==0
  assert (effect.read_bytes() if effect.exists() else b'')==before
  assert run(cold,'retry').returncode==0 and not (cold/'effect.jsonl').exists()
  results.append({'interruption':mode,'exit_code':exitcode,'retained_status':state,'synthetic_effects':len(before.splitlines()),'fresh_process_repeated_effect':False,'cold_copy_repeated_effect':False})
print(json.dumps({'candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Synthetic approval schema and remote callback; post-claim cold copies only. Pre-claim old backup, selected-number paths, real mailbox reconciliation and UI visibility remain unverified.'}))
