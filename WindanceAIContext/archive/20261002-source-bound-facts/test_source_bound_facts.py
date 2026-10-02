import sqlite3,tempfile,unittest
from pathlib import Path
import owned_fact_store as store
from memory_ingress_policy import Policy,Resolver,Denied
from source_bound_facts import Source,install,record_statement,read_verified,manager_source_loader

class SourceBinding(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');store.install(self.c);install(self.c)
  self.r=Resolver([Policy('fixture','fixture-token',frozenset([('william','fixture','personal','write')]))])
  self.source=Source('william','fixture','manager-message:one','Remember this: synthetic preference')
  self.load=lambda owner,ref:self.source
 def tearDown(self):self.c.close()
 def write(self,**changes):
  args=dict(event_id='event1',owner='william',channel='fixture',scope='personal',kind='preference',key='same',source_ref='manager-message:one',quote='synthetic preference')
  args.update(changes)
  return record_statement(self.r,self.c,'Bearer fixture-token',self.load,lambda value:'password' not in value,**args)
 def read(self):return read_verified(self.c,'william','william','personal','preference','same',self.load)
 def test_source_and_fact_atomic_and_retrievable(self):
  self.write();self.assertEqual(self.read()['value'],'synthetic preference');self.assertTrue(self.write()['replayed'])
  self.assertEqual(self.c.execute('SELECT count(*) FROM owned_fact_sources').fetchone()[0],1)
 def test_forged_quote_and_owner_rejected(self):
  with self.assertRaises(ValueError):self.write(quote='fabricated claim')
  self.source=Source('shawn','fixture','manager-message:one','synthetic preference')
  with self.assertRaises(PermissionError):self.write()
  self.assertEqual(self.c.execute('SELECT count(*) FROM owned_facts').fetchone()[0],0)
 def test_source_drift_withheld_and_corrected(self):
  self.write();self.source=Source('william','fixture','manager-message:one','Remember this: corrected preference')
  self.assertIsNone(self.read())
  self.write(event_id='event2',quote='corrected preference',expected_revision=1)
  self.assertEqual(self.read()['value'],'corrected preference')
 def test_changed_source_cannot_reuse_event(self):
  self.write();self.source=Source('william','fixture','manager-message:one','New context: synthetic preference')
  with self.assertRaises(store.Conflict):self.write()
 def test_source_failure_rolls_back_fact_and_request(self):
  self.c.execute("CREATE TRIGGER source_failure BEFORE INSERT ON owned_fact_sources BEGIN SELECT RAISE(ABORT,'fixture'); END")
  with self.assertRaises(sqlite3.IntegrityError):self.write()
  for table in ['owned_facts','owned_fact_requests','owned_fact_events']:self.assertEqual(self.c.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
 def test_source_changes_during_transaction_roll_back(self):
  original=self.source;calls=[]
  def changing(*args):
   calls.append(1)
   return original if len(calls)==1 else Source('william','fixture','manager-message:one','Changed context: synthetic preference')
  self.load=changing
  with self.assertRaises(store.Conflict):self.write()
  self.assertEqual(self.c.execute('SELECT count(*) FROM owned_facts').fetchone()[0],0)
 def test_rejected_content_not_recorded(self):
  self.source=Source('william','fixture','manager-message:one','Remember this: password fixture')
  with self.assertRaises(ValueError):self.write(quote='password fixture')
  self.assertEqual(self.c.execute('SELECT count(*) FROM owned_fact_sources').fetchone()[0],0)
 def test_missing_source_and_deleted_fact_withheld(self):
  self.write()
  def missing(*args):raise KeyError('fixture')
  self.assertIsNone(read_verified(self.c,'william','william','personal','preference','same',missing))
  store.write(self.c,'william','william','personal','preference','same',None,'deletion-fixture',1,delete=True)
  self.assertIsNone(self.read())
 def test_auth_precedes_source_access(self):
  def forbidden(*args):raise AssertionError('Unauthorized source read')
  self.load=forbidden
  with self.assertRaises(Denied):self.write(owner='shawn')
 def test_manager_loader_checks_actual_schema_owner(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'manager.db'
   c=sqlite3.connect(path);c.execute('CREATE TABLE messages(id TEXT,owner TEXT,channel TEXT,request TEXT)')
   c.execute('INSERT INTO messages VALUES(?,?,?,?)',('one','William','fixture','synthetic preference'));c.commit();c.close()
   load=manager_source_loader(lambda:sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True))
   self.assertEqual(load('william','manager-message:one').text,'synthetic preference')
   with self.assertRaises(PermissionError):load('shawn','manager-message:one')

if __name__=='__main__':unittest.main()
