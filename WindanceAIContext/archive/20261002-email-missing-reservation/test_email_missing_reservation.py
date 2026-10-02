"""Older/unpaired intent evidence must still block new mailbox mutations."""
import json,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from email_mailbox_admission import SCHEMA,claim,is_held,MailboxHeld
results=[]
for mode in ['legacy_auto_unknown','legacy_approved_unknown','orphan_reservation','confirmed_history']:
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'fixture.db'
  def connect():return sqlite3.connect(path)
  with closing(connect()) as c:
   c.executescript(SCHEMA+'''CREATE TABLE email_action_intents(operation_key TEXT PRIMARY KEY,state TEXT);
CREATE TABLE email_approved_item_intents(root_approval_id TEXT,root_item_index INTEGER,state TEXT);''')
   if mode=='legacy_auto_unknown':c.execute("INSERT INTO email_action_intents VALUES('old','unconfirmed')")
   if mode=='legacy_approved_unknown':c.execute("INSERT INTO email_approved_item_intents VALUES('old',0,'unconfirmed')")
   if mode=='orphan_reservation':c.execute("INSERT INTO email_mailbox_admission(mailbox,operation_key) VALUES('william','orphan')")
   if mode=='confirmed_history':c.execute("INSERT INTO email_action_intents VALUES('old','confirmed')")
   c.commit()
  assert is_held(connect)==(mode!='confirmed_history')
  with closing(connect()) as c:
   c.execute('BEGIN IMMEDIATE')
   try:claim(c,'new')
   except MailboxHeld:assert mode!='confirmed_history'
   else:assert mode=='confirmed_history'
   c.rollback()
   assert c.execute('SELECT COUNT(*) FROM email_mailbox_admission').fetchone()[0]==(1 if mode=='orphan_reservation' else 0)
  results.append({'case':mode,'new_mutation_held':mode!='confirmed_history','historical_evidence_unchanged':True})
print(json.dumps({'cases':results,'actual_mailbox_calls':0,'production_changes':False,'limits':'Does not reconstruct missing intent history or resolve orphan holds. Old snapshots predating all intent evidence need external reconciliation.'}))
