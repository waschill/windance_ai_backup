import json
import sqlite3
import unittest
import memory_ingress_policy as ingress
import owned_fact_store as store
from source_fact_gateway import apply_fact_request


class DurableRequest(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:');store.install(self.c)
        self.resolver=ingress.Resolver([ingress.Policy('fixture','fixture-token',frozenset(
            ('william','fixture','personal',op) for op in ['write','delete']))])
    def tearDown(self):self.c.close()
    def apply(self,event='one',value='PRIVATE_FIXTURE',revision=0,delete=False):
        return apply_fact_request(self.resolver,self.c,'Bearer fixture-token',event_id=event,owner='william',
            channel='fixture',scope='personal',kind='preference',key='same',value=value,expected_revision=revision,delete=delete)
    def test_source_and_fact_commit_together(self):
        receipt=self.apply();fact=store.read(self.c,'william','william','personal','preference','same')
        self.assertEqual(fact['source_ref'],receipt['source_ref'])
        self.assertEqual(self.c.execute('SELECT owner FROM owned_fact_requests').fetchone()[0],'william')
    def test_retry_reuses_receipt_without_rewriting(self):
        first=self.apply();again=self.apply()
        self.assertFalse(first['replayed']);self.assertTrue(again['replayed'])
        self.assertEqual(again['revision'],1)
        self.assertEqual(self.c.execute('SELECT count(*) FROM owned_fact_events').fetchone()[0],1)
    def test_changed_request_under_same_id_rejected(self):
        self.apply()
        with self.assertRaises(store.Conflict):self.apply(value='changed')
        self.assertEqual(store.read(self.c,'william','william','personal','preference','same')['value'],'PRIVATE_FIXTURE')
    def test_receipt_failure_rolls_back_source_and_fact(self):
        self.c.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON owned_fact_requests BEGIN SELECT RAISE(ABORT,'fixture'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.apply()
        for table in ['owned_facts','owned_fact_events','owned_fact_requests']:
            self.assertEqual(self.c.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
    def test_retry_after_correction_or_deletion_never_resurrects_old_value(self):
        self.apply();self.apply('two','corrected',1)
        self.assertTrue(self.apply()['superseded'])
        self.apply('three',None,2,True)
        self.assertTrue(self.apply()['superseded'])
        self.assertIsNone(store.read(self.c,'william','william','personal','preference','same'))
        self.assertNotIn('PRIVATE_FIXTURE',json.dumps(self.c.execute('SELECT * FROM owned_fact_requests').fetchall()))
    def test_missing_event_id_rejected(self):
        with self.assertRaises(ValueError):self.apply(event='')


if __name__=='__main__':unittest.main()
