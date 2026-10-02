"""Two splits preserve original identity; tampered lineage stays held."""
import json,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from email_approval_selection import SCHEMA,claim
from email_approval_lineage import resolve,LineageHeld
results=[]
for mode in ['valid','changed_child','changed_digest','ambiguous_parent','changed_expiry','changed_partition']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db'
  def connect():return sqlite3.connect(path)
  original={'id':'root','action':'gmail.batch','requested_at':'time','payload_json':json.dumps({'actions':[{'action':'gmail.delete','message_id':f'fixture-{i}'} for i in range(4)],'_expires_at':'expiry'})}
  with closing(connect()) as c:
   c.execute('CREATE TABLE approvals(id TEXT PRIMARY KEY,action TEXT,payload_json TEXT,status TEXT,requested_at TEXT,decided_at TEXT,decision_note TEXT)');c.executescript(SCHEMA)
   c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES(?,?,?,'pending',?)",(original['id'],original['action'],original['payload_json'],original['requested_at']));c.commit()
  first=claim(connect,original,[0],[],lambda a:True,lambda:'later')
  with closing(connect()) as c:
   r=c.execute('SELECT id,action,payload_json,requested_at FROM approvals WHERE id=?',(first['child_approval_id'],)).fetchone();child=dict(zip(['id','action','payload_json','requested_at'],r))
  second=claim(connect,child,[0],[1],lambda a:True,lambda:'later')
  leaf=second['child_approval_id']
  with closing(connect()) as c:
   if mode in {'changed_child','changed_expiry'}:
    payload=json.loads(c.execute('SELECT payload_json FROM approvals WHERE id=?',(leaf,)).fetchone()[0]);payload['_expires_at' if mode=='changed_expiry' else 'actions']='changed'
    c.execute('UPDATE approvals SET payload_json=? WHERE id=?',(json.dumps(payload),leaf))
   if mode=='changed_digest':c.execute("UPDATE email_approval_selections SET selection_sha256='changed' WHERE child_approval_id=?",(leaf,))
   if mode=='changed_partition':c.execute("UPDATE email_approval_selections SET remaining_indexes_json='[0]' WHERE child_approval_id=?",(leaf,))
   if mode=='ambiguous_parent':c.execute('INSERT INTO email_approval_selections SELECT ?,selection_sha256,selected_indexes_json,rejected_indexes_json,remaining_indexes_json,child_approval_id,created_at FROM email_approval_selections WHERE child_approval_id=?',('other-parent',leaf))
   c.commit()
  try:
   identity=resolve(connect,leaf,0)
   assert mode=='valid' and identity['root_approval_id']=='root' and identity['root_item_index']==3 and identity['lineage_depth']==2
   assert identity['action_sha256']==resolve(connect,'root',3)['action_sha256']
   state='resolved'
  except LineageHeld:assert mode!='valid';state='held'
  results.append({'case':mode,'state':state})
print(json.dumps({'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Identity/provenance only; no execution permission, per-item receipt ledger or operator route. Database provenance deletion cannot be detected without stronger retained anchors.'}))
