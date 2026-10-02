import sqlite3
import unittest
from dataclasses import FrozenInstanceError
import memory_ingress_policy as ingress
import owned_fact_store as store


def policy(issuer, owner, channel='owner-session', scope='personal', operations=('read','write','delete')):
    return ingress.Policy(issuer, 'fixture-'+issuer, frozenset((owner,channel,scope,op) for op in operations))


class IngressContract(unittest.TestCase):
    def setUp(self):
        self.resolver=ingress.Resolver([policy('a','william'),policy('b','shawn'),
            policy('service','william','fixture-sam','business',('write',))])
        self.db=sqlite3.connect(':memory:');store.install(self.db)
    def tearDown(self): self.db.close()
    def save(self, credential='a', owner='william', **extra):
        args=dict(owner=owner,channel='owner-session',scope='personal',kind='habit',key='same',
                  value='fixture-'+str(owner),source_ref='fixture:source')
        args.update(extra)
        return ingress.save_fact(self.resolver,self.db,'Bearer fixture-'+credential,**args)
    def test_actual_store_equal_key_isolation(self):
        self.save();self.save('b','shawn')
        a=ingress.read_fact(self.resolver,self.db,'Bearer fixture-a',actor='william',channel='owner-session',scope='personal',fact_owner='william',kind='habit',key='same',source_ref='fixture:read')
        self.assertEqual(a['value'],'fixture-william')
        self.assertIsNone(ingress.read_fact(self.resolver,self.db,'Bearer fixture-b',actor='shawn',channel='owner-session',scope='personal',fact_owner='william',kind='habit',key='same',source_ref='fixture:read'))
    def test_claimed_owner_cannot_override_credential(self):
        with self.assertRaises(ingress.Denied): self.save('b','william')
        self.assertEqual(self.db.execute('SELECT count(*) FROM owned_facts').fetchone()[0],0)
    def test_missing_unknown_malformed_credentials(self):
        for token in [None,'','Bearer unknown','Bearer ü','Basic fixture-a']:
            with self.subTest(token=token),self.assertRaises(ingress.Denied):
                self.resolver.bind(token,owner='william',channel='owner-session',scope='personal',operation='write',source_ref='fixture:source')
    def test_no_owner_default_and_wrong_channel(self):
        for changes in [{'owner':None},{'channel':'max-imessage'},{'scope':'business'}]:
            with self.subTest(changes=changes), self.assertRaises(ingress.Denied):self.save(**changes)
    def test_background_service_cannot_read_or_write_personal(self):
        self.save('service',channel='fixture-sam',scope='business')
        with self.assertRaises(ingress.Denied): self.save('service',channel='fixture-sam')
        with self.assertRaises(ingress.Denied):
            self.resolver.bind('Bearer fixture-service',owner='william',channel='fixture-sam',scope='business',operation='read',source_ref='fixture:read')
    def test_correction_and_delete_through_bound_identity(self):
        self.save();self.save(value='corrected',expected_revision=1)
        self.save(value=None,expected_revision=2,delete=True)
        self.assertIsNone(store.read(self.db,'william','william','personal','habit','same'))
    def test_revocation_and_ambiguous_configuration(self):
        revoked=ingress.Resolver([])
        with self.assertRaises(ingress.Denied):
            revoked.bind('Bearer fixture-a',owner='william',channel='owner-session',scope='personal',operation='read',source_ref='fixture:read')
        with self.assertRaises(ValueError): ingress.Resolver([policy('a','william'),policy('a','shawn')])
    def test_multiowner_adapter_has_only_explicit_combinations(self):
        resolver=ingress.Resolver([ingress.Policy('adapter','fixture-adapter',frozenset({
            ('william','direct-william','personal','write'),('shawn','direct-shawn','personal','write')}))])
        self.assertEqual(resolver.bind('Bearer fixture-adapter',owner='shawn',channel='direct-shawn',scope='personal',operation='write',source_ref='fixture:row').owner,'shawn')
        with self.assertRaises(ingress.Denied):
            resolver.bind('Bearer fixture-adapter',owner='william',channel='direct-shawn',scope='personal',operation='write',source_ref='fixture:row')
    def test_credentials_not_in_repr_and_identity_immutable(self):
        self.assertNotIn('fixture-a',repr(self.resolver.policies[0]))
        result=self.resolver.bind('Bearer fixture-a',owner='william',channel='owner-session',scope='personal',operation='read',source_ref='fixture:read')
        with self.assertRaises(FrozenInstanceError):result.owner='shawn'


if __name__=='__main__':unittest.main()
