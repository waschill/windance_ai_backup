import sqlite3
import unittest
import bridge_sender_boundary as bridge
import memory_ingress_policy as ingress
import owned_fact_store as store


class SenderMemoryChain(unittest.TestCase):
    def setUp(self):
        self.messages=sqlite3.connect(':memory:')
        self.messages.executescript('''CREATE TABLE message(ROWID INTEGER PRIMARY KEY,text TEXT,handle_id INTEGER,is_from_me INTEGER);
        CREATE TABLE handle(ROWID INTEGER PRIMARY KEY,id TEXT);
        CREATE TABLE chat(ROWID INTEGER PRIMARY KEY,style INTEGER,room_name TEXT);
        CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);
        CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);
        INSERT INTO handle VALUES(1,'+1 (202) 555-0101'),(2,'+1 (202) 555-0102'),(3,'12025550101@example.test');''')
        self.facts=sqlite3.connect(':memory:');store.install(self.facts)
        self.allowed={'12025550101':'william','12025550102':'shawn'}
        self.policy=ingress.Resolver([ingress.Policy('fixture-bridge','fixture-token',frozenset(
          (owner,'max-imessage','personal','write') for owner in ['william','shawn']))])
    def tearDown(self):self.messages.close();self.facts.close()
    def row(self,mid,handle=1,participants=None,style=45,room='',chat=True,outgoing=0):
        self.messages.execute('INSERT INTO message VALUES(?,?,?,?)',(mid,'synthetic fact',handle,outgoing))
        if chat:
            self.messages.execute('INSERT INTO chat VALUES(?,?,?)',(mid,style,room))
            self.messages.execute('INSERT INTO chat_message_join VALUES(?,?)',(mid,mid))
            for h in participants if participants is not None else [handle]:
                self.messages.execute('INSERT INTO chat_handle_join VALUES(?,?)',(mid,h))
    def process(self):
        accepted=[];seen=[]
        for rowid,text,sender,direct in bridge.pending_messages(self.messages,0):
            seen.append(rowid);owner=bridge.mapped_owner(sender,direct,self.allowed)
            if owner is None:continue
            ingress.save_fact(self.policy,self.facts,'Bearer fixture-token',owner=owner,channel='max-imessage',
              scope='personal',kind='fixture',key=str(rowid),value=text,source_ref='fixture:message:'+str(rowid))
            accepted.append(owner)
        return accepted,seen
    def test_direct_both_owners_and_source_readback(self):
        self.row(1);self.row(2,handle=2)
        self.assertEqual(self.process()[0],['william','shawn'])
        self.assertEqual(store.read(self.facts,'shawn','shawn','personal','fixture','2')['source_ref'],'fixture:message:2')
        self.assertIsNone(store.read(self.facts,'william','shawn','personal','fixture','2'))
    def test_group_unknown_ambiguous_missing_and_wrong_member(self):
        self.row(1,participants=[1,2]);self.row(2,style=43);self.row(3,chat=False)
        self.row(4,participants=[2]);self.row(5,room='fixture-room');self.row(6)
        self.messages.execute('INSERT INTO chat_message_join VALUES(?,?)',(1,6))
        accepted,seen=self.process()
        self.assertEqual(accepted,[]);self.assertEqual(seen,[1,2,3,4,5,6])
        self.assertEqual(self.facts.execute('SELECT count(*) FROM owned_facts').fetchone()[0],0)
    def test_email_digit_collision_rejected(self):
        self.row(1,handle=3)
        self.assertEqual(self.process()[0],[])
        self.assertEqual(''.join(c for c in '12025550101@example.test' if c.isdigit()),'12025550101')
    def test_outgoing_and_cursor_boundaries(self):
        self.row(1);self.row(2,outgoing=1);self.row(3,handle=2)
        self.assertEqual([r[0] for r in bridge.pending_messages(self.messages,1)],[3])
    def test_normalization_no_unicode_or_unenrolled_email(self):
        self.assertEqual(bridge.normalize_sender('+1 (202) 555-0101'),'12025550101')
        for value in ['١٢٠٢٥٥٥٠١٠١','12025550101@example.test','',None,'123','call12025550101']:
            self.assertEqual(bridge.normalize_sender(value),'')
    def test_allowlist_and_direct_metadata_both_required(self):
        self.assertIsNone(bridge.mapped_owner('+1 202 555 0199',1,self.allowed))
        self.assertIsNone(bridge.mapped_owner('+1 202 555 0101',0,self.allowed))


if __name__=='__main__':unittest.main()
