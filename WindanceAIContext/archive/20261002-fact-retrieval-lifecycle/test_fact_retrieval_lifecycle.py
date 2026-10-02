import sqlite3
import unittest
import owned_fact_store as store


class RetrievalLifecycle(unittest.TestCase):
    def setUp(self):self.c=sqlite3.connect(':memory:');store.install(self.c)
    def tearDown(self):self.c.close()
    def put(self,owner='william',scope='business',key='same',value='old',revision=0):
        return store.write(self.c,owner,owner,scope,'fixture',key,value,'fixture:source',revision)
    def list(self,actor='william',scopes=('business',),limit=100):
        return store.visible_facts(self.c,actor,scopes=scopes,limit=limit)
    def share(self,revoke=False):store.share(self.c,'william','william','business','fixture','same','shawn',1,revoke=revoke)
    def test_correction_deletion_and_stale_cache_cannot_resurrect(self):
        self.put();self.c.execute('CREATE TABLE stale_vectors(text TEXT)')
        self.c.execute("INSERT INTO stale_vectors VALUES('old')");self.c.commit()
        self.put(value='corrected',revision=1)
        self.assertEqual([x['value'] for x in self.list()],['corrected'])
        store.write(self.c,'william','william','business','fixture','same',None,'fixture:deletion',2,delete=True)
        self.assertEqual(self.list(),[])
        self.assertEqual(self.c.execute('SELECT text FROM stale_vectors').fetchone()[0],'old')
    def test_scope_separation_and_explicit_sharing_lifecycle(self):
        self.put();self.put(scope='personal',value='personal')
        self.assertEqual(self.list('shawn'),[])
        self.share();self.assertEqual([r['value'] for r in self.list('shawn')],['old'])
        self.assertEqual(self.list('shawn',('personal',)),[])
        self.share(True);self.assertEqual(self.list('shawn'),[])
        self.assertEqual([r[0] for r in self.c.execute('SELECT action FROM owned_fact_grant_events ORDER BY event_id')],['grant','revoke'])
    def test_correction_revokes_and_audits_existing_grant(self):
        self.put();self.share();self.put(value='private revision',revision=1)
        self.assertEqual(self.list('shawn'),[])
        self.assertEqual([r[0] for r in self.c.execute('SELECT action FROM owned_fact_grant_events ORDER BY event_id')],['grant','invalidate'])
    def test_grant_audit_failure_rolls_back_access(self):
        self.put();self.c.execute("CREATE TRIGGER fail_grant BEFORE INSERT ON owned_fact_grant_events BEGIN SELECT RAISE(ABORT,'fixture'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.share()
        self.assertEqual(self.list('shawn'),[])
    def test_repeated_grant_is_idempotent(self):
        self.put();self.share();self.share()
        self.assertEqual(self.c.execute('SELECT count(*) FROM owned_fact_grant_events').fetchone()[0],1)
    def test_foreign_flood_does_not_consume_limit(self):
        self.put()
        for i in range(510):self.put(owner='shawn',key=str(i))
        self.assertEqual(len(self.list(limit=1)),1)
        self.assertEqual(self.list(limit=1)[0]['owner'],'william')
    def test_missing_identity_scope_and_invalid_limit_rejected(self):
        with self.assertRaises(PermissionError):self.list(None)
        for scopes in [(),('unknown',),'business']:
            with self.assertRaises(ValueError):self.list(scopes=scopes)
        with self.assertRaises(ValueError):self.list(limit=0)
    def test_equal_keys_have_distinct_source_ids(self):
        self.put();self.put(scope='personal')
        self.assertEqual(len({r['source_id'] for r in self.list(scopes=('business','personal'))}),2)


if __name__=='__main__':unittest.main()
