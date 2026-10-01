import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

MODULE=Path(__file__).with_name('memory_owner_boundary.py')
spec=importlib.util.spec_from_file_location('memory_owner_candidate',MODULE)
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)

class MemoryOwnerTests(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row
        self.c.executescript('''
        CREATE TABLE vector_memory(id TEXT,source_type TEXT,source_id TEXT,title TEXT,text TEXT,embedding_json TEXT,embedding_model TEXT,updated_at TEXT);
        CREATE TABLE conversations(id TEXT PRIMARY KEY,user TEXT,channel TEXT,message TEXT,response TEXT);
        CREATE TABLE staff_tasks(id TEXT PRIMARY KEY,requester TEXT,assignee TEXT,title TEXT,request TEXT,result TEXT,status TEXT);
        ''')
    def tearDown(self):self.c.close()
    def conversation(self,identifier,owner,text='synthetic',at='2026-10-01',derived=None):
        self.c.execute('insert into conversations values (?,?,?,?,?)',(identifier,owner,'synthetic',text,'answer'))
        stored=derived or f'{owner}: {text}\n\nHerald: answer'
        self.c.execute('insert into vector_memory values (?,?,?,?,?,?,?,?)',('conversation:'+identifier,'conversation',identifier,'untrusted title',stored,'[1,0]','synthetic',at))
    def test_both_directions(self):
        for who in ['William','Shawn']:self.conversation(who,who)
        for who in ['William','Shawn']:
            rows=policy.owned_memory_rows(self.c,who)
            self.assertEqual([r['source_id'] for r in rows],[who]);self.assertEqual(rows[0]['source_owner'],who)
    def test_unknown_scope_denied(self):
        self.conversation('w','William')
        for who in [None,'','unknown','William OR 1=1']:
            self.assertEqual(policy.owned_memory_rows(self.c,who),[])
    def test_owner_filter_precedes_limit(self):
        self.conversation('older-own','William',at='2020')
        for i in range(501):self.conversation(str(i),'Shawn',at='2026')
        self.assertEqual(policy.owned_memory_rows(self.c,'William',1)[0]['source_id'],'older-own')
    def test_orphan_and_unclassified_facts_withheld(self):
        for kind in ['conversation','memory','ops_item']:
            self.c.execute('insert into vector_memory values (?,?,?,?,?,?,?,?)',(kind,kind,'missing','William','private','[1,0]','synthetic','2026'))
        self.assertEqual(policy.owned_memory_rows(self.c,'William'),[])
    def test_wrong_derived_prefix_does_not_change_owner(self):
        self.conversation('s','Shawn',derived='William: synthetic\n\nHerald: answer')
        row=policy.owned_memory_rows(self.c,'Shawn')[0]
        self.assertTrue(row['text'].startswith('Shawn:'));self.assertFalse(row['derived_text_matches_source']);self.assertIsNone(row['embedding_json'])
        self.assertEqual(policy.owned_memory_rows(self.c,'William'),[])
    def test_corrected_source_text_replaces_old_derived_text(self):
        self.conversation('w','William',text='old sensitive fact')
        self.c.execute("update conversations set message='corrected fact' where id='w'")
        row=policy.owned_memory_rows(self.c,'William')[0]
        self.assertNotIn('old sensitive fact',row['text']);self.assertIn('corrected fact',row['text']);self.assertIsNone(row['embedding_json'])
    def test_source_delete_revokes_retrieval(self):
        self.conversation('w','William');self.c.execute("delete from conversations where id='w'")
        self.assertEqual(policy.owned_memory_rows(self.c,'William'),[])
    def test_source_owner_change_revokes_old_owner(self):
        self.conversation('w','William');self.c.execute("update conversations set user='Shawn' where id='w'")
        self.assertEqual(policy.owned_memory_rows(self.c,'William'),[])
        self.assertEqual(policy.owned_memory_rows(self.c,'Shawn')[0]['source_owner'],'Shawn')
    def test_current_embedding_retained(self):
        self.conversation('w','William');row=policy.owned_memory_rows(self.c,'William')[0]
        self.assertTrue(row['derived_text_matches_source']);self.assertEqual(row['embedding_json'],'[1,0]')
    def test_task_requester_is_authority_not_title(self):
        self.c.execute('insert into staff_tasks values (?,?,?,?,?,?,?)',('task','William','Forge','Shawn title','synthetic request','synthetic result','completed'))
        self.c.execute('insert into vector_memory values (?,?,?,?,?,?,?,?)',('task','staff_task','task','Shawn owns this','stale text','[1,0]','synthetic','2026'))
        self.assertEqual(policy.owned_memory_rows(self.c,'Shawn'),[])
        row=policy.owned_memory_rows(self.c,'William')[0]
        self.assertIn('synthetic result',row['text']);self.assertEqual(row['access_scope'],'private')
    def test_selection_does_not_change_source_or_derived_rows(self):
        self.conversation('s','Shawn',derived='William: wrong attribution')
        before='\n'.join(self.c.iterdump());policy.owned_memory_rows(self.c,'Shawn')
        self.assertEqual('\n'.join(self.c.iterdump()),before)

if __name__=='__main__':unittest.main(verbosity=2)
