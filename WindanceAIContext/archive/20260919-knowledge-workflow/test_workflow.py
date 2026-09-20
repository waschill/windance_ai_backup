import ast
import asyncio
import contextlib
import datetime as dt
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import types
import unittest
import uuid
import decision_records as records
import windance_weekly_stack_review as weekly


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.db'
        @contextlib.contextmanager
        def db():
            with contextlib.closing(sqlite3.connect(self.path)) as conn:
                conn.row_factory = sqlite3.Row
                yield conn
        self.db = db
        with db() as conn:
            conn.executescript('CREATE TABLE captures(id TEXT PRIMARY KEY,original_text TEXT,source_channel TEXT,source_user TEXT,state TEXT,created_at TEXT,updated_at TEXT,discarded_at TEXT);CREATE TABLE capture_events(id INTEGER PRIMARY KEY,capture_id TEXT,event_type TEXT,actor TEXT,note TEXT,created_at TEXT);')
        self.ns = dict(db=db, now=lambda: dt.datetime.now(dt.timezone.utc).isoformat(), dt=dt, uuid=uuid, re=re,
            Any=object, Header=lambda **kw:None, audit=lambda *a:None, IDEA_STATES={'active','hold','discussion','archived'},
            require_token=lambda x:None, redact_approval_auth_word=lambda x:x, redact_level8_code=lambda x:x, auth_word_matches=lambda x:False)
        tree = ast.parse(Path('agent_harness.py').read_text(encoding='utf-8'))
        names = {'create_capture','create_idea','list_ideas','review_idea','memory_looks_secret','message'}
        nodes = [x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name in names]
        for node in nodes:
            node.decorator_list=[]
        unit = ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+nodes,type_ignores=[])
        exec(compile(ast.fix_missing_locations(unit),'<extracted-live-functions>','exec'),self.ns)

    def tearDown(self): self.temp.cleanup()

    def test_capture_archive_restore_and_original(self):
        create=self.ns['create_idea']; review=self.ns['review_idea']; listing=self.ns['list_ideas']
        item=create('Maybe improve scheduling', 'test', 'William')
        review(item['id'],'archived','Duplicate of existing scheduler','Vega')
        self.assertEqual(listing('archived')[0]['original_text'],'Maybe improve scheduling')
        review(item['id'],'active','Revisit with new evidence','William')
        self.assertEqual(len(listing('active')[0]['history']),3)

    def test_private_exclusion_pagination_and_invalid_review(self):
        private=self.ns['create_capture']('Private text','test','William','private')
        for i in range(4):self.ns['create_idea'](f'Idea {i}','test','William')
        self.assertEqual(len(self.ns['list_ideas']('',2,2)),2)
        self.assertNotIn(private['id'],[x['id'] for x in self.ns['list_ideas']()])
        with self.assertRaises(KeyError):self.ns['review_idea'](private['id'],'active','Expose','Vega')
        with self.assertRaises(ValueError):self.ns['review_idea']('x','archived','','Vega')
        with self.assertRaises(ValueError):self.ns['create_idea']('password example','test','William')

    def test_message_capture_does_not_dispatch(self):
        for text in ['Idea: build a new dashboard','Herald, Add to the Idea Board: delete the old service later']:
            reply=asyncio.run(self.ns['message'](types.SimpleNamespace(message=text,channel='test',user='William'),None,None))
            self.assertEqual(reply['provider'],'idea-board')
        self.assertEqual(len(self.ns['list_ideas']()),2)

    def test_decision_required_fields_and_signoff(self):
        d=valid_decision()
        self.assertEqual(records.parse_decisions('PASS\nDECISION_LOG_JSON: '+json.dumps({'decisions':[d]})),[d])
        del d['success_measure']
        with self.assertRaises(ValueError):records.parse_decisions('DECISION_LOG_JSON: '+json.dumps({'decisions':[d]}))
        self.assertFalse(records.signed({'status':'completed','result':'READY_TO_SEND: yes\nREADY_TO_SEND: no'},'READY_TO_SEND'))
        self.assertFalse(records.signed({'status':'partial','result':'SIGNOFF: yes'},'SIGNOFF'))

    def test_full_weekly_flow_and_fail_closed(self):
        original={name:getattr(weekly,name) for name in ['current_stack_snapshot','current_release_evidence','create_task','run_local_profile_task','synthesize_report','post_json','get_json','send_telegram']}
        try:
            for broken in [None,'Archivist','Herald','readback']:
                saved={}; sent=[]
                weekly.current_stack_snapshot=lambda:'Synthetic snapshot'
                weekly.current_release_evidence=lambda:'Synthetic evidence'
                weekly.synthesize_report=lambda *a:'A proposed feature'
                def create(role,title,request,source):
                    return {'id':str(uuid.uuid4()),'assignee':role,'source':source,'title':title}
                def run(task,timeout_seconds):
                    role=task['assignee']
                    task.update(status='completed',result={'Forge':'PASS\nDECISION_LOG_JSON: '+json.dumps({'decisions':[valid_decision()]}),'Athena':'PASS\nREADY_TO_SEND: yes','Herald':'PASS\nSIGNOFF: yes','Archivist':'PASS\npreserved decision log','Scout':'PASS'}[role])
                    if role==broken:task['status']='partial'
                    return task
                weekly.create_task=create;weekly.run_local_profile_task=run
                weekly.post_json=lambda url,payload: saved.update(payload) or {'status':'ok'}
                weekly.get_json=lambda url:{'items':[] if broken=='readback' else [json.loads(saved['value'])]}
                weekly.send_telegram=lambda text:sent.append(text) or {'ok':True}
                output=weekly.run_review(55)
                self.assertEqual(len(sent), 1 if broken is None else 0, output)
                if broken is None:self.assertFalse(json.loads(saved['value'])['implementation_authorized'])
        finally:
            for name,value in original.items():setattr(weekly,name,value)


def valid_decision():
    return dict(topic='Synthetic test',disposition='test_first',reason='Check value',owner='Forge',next_step='Prepare a proposal',success_measure='Evidence for one bounded test',revisit_on='2026-09-25',evidence=['Synthetic fixture; no real change'])


if __name__=='__main__':unittest.main(verbosity=2)
