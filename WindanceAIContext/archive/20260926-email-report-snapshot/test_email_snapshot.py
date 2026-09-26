"""Isolated regression tests: extracted deployed functions, synthetic SQLite only."""
import ast
import contextlib
import datetime as dt
import re
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).with_name('agent_harness.fixed.py')
NAMES = {'save_email_report_refs','latest_email_ref_map','consume_latest_email_ref_map',
         'numbers_after_keywords','prepare_gmail_report_reply_actions','gmail_autonomy_report',
         'undo_email_autonomy_action'}

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.conn=sqlite3.connect(str(Path(self.tmp.name)/'test.db'))
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE max_email_report_refs (id INTEGER PRIMARY KEY,report_key TEXT,ref_num INTEGER,section TEXT,message_id TEXT,thread_id TEXT,sender TEXT,subject TEXT,created_at TEXT);
        CREATE TABLE max_email_report_consumed (report_key TEXT PRIMARY KEY,consumed_at TEXT,reason TEXT);
        CREATE TABLE email_autonomy_actions (id INTEGER PRIMARY KEY,run_id TEXT,ordinal INTEGER,message_id TEXT UNIQUE,thread_id TEXT,sender TEXT,subject TEXT,decision TEXT,action TEXT,reason TEXT,draft_id TEXT,created_at TEXT,reversed_at TEXT,reversal_result TEXT);
        ''')
        self.effects=[]
        self.approvals=[]
        self.inbox=[{'id':'original-A','from':'a@example.test','subject':'A'}, {'id':'original-B','from':'b@example.test','subject':'B'}]
        def approval(*args): self.approvals.append(args); return 'synthetic'
        self.ns=dict(Any=Any,dt=dt,re=re,uuid=uuid,db=lambda:self.conn,now=lambda:dt.datetime.now(dt.UTC).isoformat(),
            short_sender=lambda s:s,compact_subject=lambda s,*args:s,
            upsert_email_sender_rule=lambda action,ref:self.effects.append(('rule',ref['message_id'])) or 'synthetic@example.test',
            gmail_delete_message=lambda mid:self.effects.append(('trash',mid)),request_approval=approval,
            GMAIL_APPROVAL_EXPIRE_MINUTES=15,parseaddr=lambda s:('',s),compose_numbered_email_draft=lambda *a:'synthetic',
            recent_inbox_email=lambda **kw:list(self.inbox),apply_email_sender_rules=lambda items:(items,[]),
            classify_email_autonomy=lambda items:{n:{'decision':'escalate','reason':'synthetic','category':'test'} for n,_ in enumerate(items,1)},
            email_autonomy_risk_reason=lambda item:None,audit=lambda *a:None,
            gmail_untrash_to_inbox=lambda mid:self.effects.append(('restore',mid)))
        tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
        code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in NAMES],type_ignores=[])
        exec(compile(code,str(SOURCE),'exec'), self.ns)
    def tearDown(self): self.conn.close(); self.tmp.cleanup()
    def save(self,key='first',items=None):
        self.ns['save_email_report_refs'](key,[(i,'test',item) for i,item in enumerate(self.inbox if items is None else items,1)])
    def action(self,text): return self.ns['prepare_gmail_report_reply_actions'](text)
    def test_missing_snapshot_terminates(self):
        self.assertEqual(self.action('ALD 1')[2],'gmail-report-invalid'); self.assertEqual(self.effects,[])
    def test_no_legacy_fallback(self):
        self.save(); self.conn.execute('DELETE FROM email_report_active'); self.assertEqual(self.ns['latest_email_ref_map'](),{})
    def test_followups_keep_snapshot(self):
        self.save(); self.action('ALD 1'); self.action('NOD 2')
        self.assertIn(('trash','original-B'),self.effects)
        self.assertEqual(len(self.ns['latest_email_ref_map']()),2)
    def test_current_inbox_order_ignored(self):
        self.save(); self.inbox.reverse(); self.action('delete 1')
        self.assertEqual(self.approvals[0][1]['actions'][0]['message_id'],'original-A')
    def test_mixed_invalid_batch_has_no_effects(self):
        self.save(); self.assertEqual(self.action('ALD 1; delete 99')[2],'gmail-report-invalid')
        self.assertEqual(self.effects,[]); self.assertEqual(self.approvals,[])
    def test_empty_supersedes(self):
        self.save(); self.save('empty',[]); self.assertEqual(self.action('delete 1')[2],'gmail-report-invalid')
    def test_new_report_supersedes(self):
        self.save(); self.save('second',[{'id':'new-C'}]); self.action('delete 1')
        self.assertEqual(self.approvals[0][1]['actions'][0]['message_id'],'new-C')
    def test_corrupt_snapshot_terminates(self):
        self.save(); self.conn.execute('DELETE FROM max_email_report_refs WHERE ref_num=2')
        self.assertEqual(self.action('delete 1')[2],'gmail-report-invalid')
    def test_autonomy_uses_same_snapshot(self):
        self.save('old',[{'id':'wrong-old'}]); self.ns['gmail_autonomy_report'](); self.action('delete 2')
        self.assertEqual(self.approvals[0][1]['actions'][0]['message_id'],'original-B')
    def test_snapshot_failure_prevents_autonomous_actions(self):
        self.ns['save_email_report_refs']=lambda *a,**kw:(_ for _ in ()).throw(OSError('synthetic failure'))
        with self.assertRaises(OSError): self.ns['gmail_autonomy_report']()
        self.assertEqual(self.effects,[])
    def test_undo_never_uses_older_authority_report(self):
        self.ns['gmail_autonomy_report'](); self.save('new',[])
        self.assertIn('invalid',self.ns['undo_email_autonomy_action']('undo email 1')[0]); self.assertEqual(self.effects,[])
    def test_approval_is_still_required(self):
        self.save(); self.action('delete 1'); self.assertEqual(self.effects,[]); self.assertEqual(len(self.approvals),1)
    def test_incomplete_report_is_not_actionable(self):
        self.save()
        self.ns['classify_email_autonomy']=lambda *a:(_ for _ in ()).throw(RuntimeError('synthetic'))
        with self.assertRaises(RuntimeError): self.ns['gmail_autonomy_report']()
        self.assertEqual(self.action('delete 1')[2],'gmail-report-invalid')
    def test_draft_body_numbers_not_references(self):
        self.save(); self.assertEqual(self.action('draft reply to 1 saying I will call at 99')[2],'gmail-summary-actions')

if __name__=='__main__': unittest.main(verbosity=2)
