import sqlite3
import unittest
import owned_fact_store as store


class FactContract(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        store.install(self.db)

    def tearDown(self):
        self.db.close()

    def write(self, owner='william', scope='personal', value='fixture-a', revision=0):
        return store.write(self.db, owner, owner, scope, 'preference', 'same', value, 'fixture:source', revision)

    def read(self, actor='william', owner='william', scope='personal'):
        return store.read(self.db, actor, owner, scope, 'preference', 'same')

    def test_equal_keys_separate_owner_and_scope(self):
        self.write(); self.write('shawn', value='fixture-b'); self.write(scope='business', value='fixture-c')
        self.assertEqual(self.read()['value'], 'fixture-a')
        self.assertEqual(self.read('shawn', 'shawn')['value'], 'fixture-b')
        self.assertEqual(self.read(scope='business')['value'], 'fixture-c')
        self.assertIsNone(self.read('shawn'))
        self.assertIsNone(self.read('shawn', scope='business'))

    def test_correction_and_stale_edit(self):
        self.write(); self.write(value='corrected', revision=1)
        with self.assertRaises(store.Conflict): self.write(value='stale', revision=1)
        self.assertEqual(self.read()['value'], 'corrected')
        self.assertEqual(self.db.execute('SELECT count(*) FROM owned_fact_events').fetchone()[0], 2)

    def test_delete_and_explicit_recreation(self):
        self.write()
        store.write(self.db, 'william', 'william', 'personal', 'preference', 'same', None, 'fixture:deletion', 1, delete=True)
        self.assertIsNone(self.read())
        self.assertIsNone(self.db.execute('SELECT value FROM owned_facts').fetchone()[0])
        with self.assertRaises(store.Conflict): self.write()
        self.write(value='new-source', revision=2)
        self.assertEqual(self.read()['revision'], 3)

    def test_grant_revocation_and_revision_binding(self):
        self.write(scope='business')
        args=(self.db,'william','william','business','preference','same','shawn',1)
        store.share(*args)
        self.assertIsNotNone(self.read('shawn',scope='business'))
        store.share(*args,revoke=True)
        self.assertIsNone(self.read('shawn',scope='business'))
        store.share(*args)
        self.write(scope='business',value='new-private-correction',revision=1)
        self.assertIsNone(self.read('shawn',scope='business'))

    def test_unauthorized_and_missing_identity(self):
        self.write()
        with self.assertRaises(PermissionError): self.read(actor=None)
        with self.assertRaises(PermissionError):
            store.write(self.db,'shawn','william','personal','preference','same','bad','fixture:bad',1)
        with self.assertRaises(ValueError):
            store.share(self.db,'william','william','personal','preference','same','shawn',1)

    def test_event_failure_rolls_back_fact(self):
        self.db.execute("CREATE TRIGGER fail_event BEFORE INSERT ON owned_fact_events BEGIN SELECT RAISE(ABORT,'fixture'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.write()
        self.assertIsNone(self.read())

    def test_no_success_on_failed_readback(self):
        original=store.read
        try:
            store.read=lambda *args: None
            with self.assertRaises(RuntimeError): self.write()
        finally: store.read=original
        self.assertIsNone(self.read())

    def test_caller_transaction_preserved(self):
        self.db.execute('CREATE TABLE unrelated(value TEXT)')
        self.db.execute("INSERT INTO unrelated VALUES('pending')")
        with self.assertRaises(RuntimeError): self.write()
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT count(*) FROM unrelated').fetchone()[0],1)


if __name__=='__main__': unittest.main()
