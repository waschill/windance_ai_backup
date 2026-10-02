"""Atomic selected/remainder ownership under contention and failed insert."""
import json,sqlite3,tempfile,threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from email_approval_selection import SCHEMA,claim,SelectionHeld
results=[]
for mode in ['overlap','child_insert_failure','expired','whole_approval_already_claimed','reject_only']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db'
  def connect():return sqlite3.connect(path,timeout=5)
  approval={'id':'fixture','action':'gmail.batch','requested_at':'fixture','payload_json':json.dumps({'actions':[{'action':'gmail.delete','message_id':f'fixture-{i}'} for i in range(3)],'_expires_at':'unchanged-fixture','summary':['untrusted old numbering']})}
  with closing(connect()) as c:
   c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)');c.executescript(SCHEMA)
   c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES(?,?,?,'pending',?)",(approval['id'],approval['action'],approval['payload_json'],approval['requested_at']))
   if mode=='child_insert_failure':c.execute("CREATE TRIGGER fail_child BEFORE INSERT ON approvals BEGIN SELECT RAISE(ABORT,'fixture'); END")
   if mode=='whole_approval_already_claimed':c.execute("UPDATE approvals SET status='executing'")
   c.commit()
  barrier=threading.Barrier(2)
  def run(_):
   if mode=='overlap':barrier.wait(timeout=5)
   try:return claim(connect,approval,[] if mode=='reject_only' else [0],[1],lambda a:mode!='expired',lambda:'later-fixture')
   except (SelectionHeld,sqlite3.IntegrityError):return 'held'
  if mode=='overlap':
   with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,range(2)))
   assert sum(isinstance(x,dict) for x in out)==1
  else:out=[run(0)]
  success=mode in {'overlap','reject_only'}
  with closing(connect()) as c:
   parents=c.execute("SELECT status FROM approvals WHERE id='fixture'").fetchone()[0]
   children=c.execute("SELECT payload_json,requested_at FROM approvals WHERE id!='fixture'").fetchall()
   evidence=c.execute('SELECT selected_indexes_json,rejected_indexes_json,remaining_indexes_json FROM email_approval_selections').fetchall()
   assert len(children)==len(evidence)==(1 if success else 0)
   if success:
    child=json.loads(children[0][0]);assert child['_expires_at']=='unchanged-fixture' and child['summary']==[] and children[0][1]=='fixture'
    assert parents==('rejected' if mode=='reject_only' else 'executing')
    assert len(child['actions'])==(2 if mode=='reject_only' else 1)
   else:assert parents==('executing' if mode=='whole_approval_already_claimed' else 'pending')
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  results.append({'case':mode,'child_approvals':len(children),'selection_records':len(evidence),'parent_status':parents})
print(json.dumps({'cases':results,'mailbox_callbacks_available':False,'production_changes':False,'limits':'Internal component only; authentication/reference checks, display, final receipts, crash recovery and full handler integration pending.'}))
