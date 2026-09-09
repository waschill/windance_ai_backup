import asyncio
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

scratch = tempfile.TemporaryDirectory(prefix='windance-task-tests-')
for k in ['AGENT_HARNESS_CONFIG_DIR','AGENT_HARNESS_DATA_DIR','AGENT_HARNESS_LOG_DIR','GOOGLE_WORKSPACE_CONFIG_DIR']:
    os.environ[k] = str(Path(scratch.name) / k)
sys.path.insert(0, '/Users/herald/services/agent-harness')
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
h = load('candidate_harness', Path(__file__).with_name('agent_harness.py'))
r = load('candidate_runner', Path(__file__).with_name('profile_staff_runner.py'))
h.audit = lambda *a, **kw: None
h.upsert_vector_memory = lambda *a, **kw: None
# The suite must never reach a provider, cloud service or external action.
h.post_codex_shadow = lambda *a, **kw: (_ for _ in ()).throw(AssertionError('Unexpected cloud route'))

class Tests(unittest.TestCase):
    def make(self, title='continuity test'):
        return h.create_staff_task('Scout', 'Compare the supplied public documents. No external writes.', title=title, source='isolated-test')

    def test_classification(self):
        cases = {'PASS: evidence recorded':'completed','**PASS**\nEvidence: artifact':'completed',
                 'PARTIAL: source unavailable':'partial','BLOCKED: input required':'blocked',
                 'FAIL: mismatch':'failed','FAILED: runtime':'failed','Looks great':'blocked','':'blocked',
                 'PASSENGER':'blocked','\x1b[32mPARTIAL\x1b[0m: work remains':'partial'}
        for value, wanted in cases.items():
            self.assertEqual(r.classify_result(value), wanted)

    def test_profile_limits(self):
        for configured, ceiling, expected in [(30,'40',30),(100,'40',40),(15,'20',15)]:
            with patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(configured))), patch.dict(os.environ, {'PROFILE_STAFF_MAX_TURNS':ceiling}):
                self.assertEqual(r.effective_turn_limit('athena'), expected)
        for configured in [0,-1,True,'30']:
            with patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(configured))):
                with self.assertRaises(ValueError): r.effective_turn_limit('athena')

    def test_partial_cannot_complete(self):
        t=self.make()
        result=h.complete_staff_task(t['id'],'PARTIAL: one source missing','completed','test')
        self.assertEqual(result['status'],'partial')
        self.assertIsNone(result['completed_at'])
        with self.assertRaises(h.HTTPException): h.complete_staff_task(t['id'],'done','bogus')
        with self.assertRaises(h.HTTPException): h.complete_staff_task(t['id'],'','completed')
        self.assertEqual(h.complete_staff_task(t['id'],'PASS: evidence checked')['status'],'completed')

    def test_shared_packet_and_notes(self):
        t=self.make('shared handoff unique')
        response=asyncio.run(h.message(h.MessageIn(message='update task shared handoff unique: Use document B instead of A.',channel='chat'),None))
        self.assertEqual(response['task']['id'],t['id'])
        # Walkie uses this same /message payload. No model or new worker is called.
        response=asyncio.run(h.message(h.MessageIn(message='show task shared handoff unique',channel='walkie'),None))
        self.assertEqual(response['provider'],'task-ledger')
        self.assertIn('document B',response['reply'])
        api=h.get_staff_task(t['id'])['task']
        self.assertEqual(api,response['task'])
        self.assertIn('document B',r.task_prompt(api))
        self.assertEqual(api['status'],'pending')
        with h.db() as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM staff_tasks WHERE id=?',(t['id'],)).fetchone()[0],1)

    def test_ambiguity_and_privacy(self):
        self.make('duplicated title'); self.make('duplicated title')
        self.assertIsNone(h.resolve_task_reference('duplicated title'))
        self.assertIsNone(h.resolve_task_reference('%'))
        self.assertIsNone(h.task_continuity_reply('show my work','shawn','chat'))
        t=h.create_staff_task('Iris','Private scoped test',requester='Shawn',title='other person')
        self.assertIsNone(h.resolve_task_reference(t['id']))
        t=self.make('secret filter')
        with self.assertRaises(h.HTTPException): h.append_task_note(t['id'],'a password should not be saved')
        self.assertIsNone(h.task_continuity_reply('approve 1234','william','chat'))
        self.assertIsNone(h.task_continuity_reply('delete email 2','william','chat'))

    def test_claim_still_atomic(self):
        t=self.make()
        h.start_staff_task(t['id'])
        with self.assertRaises(h.HTTPException): h.start_staff_task(t['id'])

    def test_board_escapes_untrusted_text(self):
        t=self.make('<script>alert(1)</script>')
        response=h.staff_work_board(t['id'])
        self.assertNotIn('<script>',response.body.decode())
        self.assertIn('&lt;script&gt;',response.body.decode())
        self.assertEqual(response.headers['cache-control'],'no-store')

    def test_actual_http_routes(self):
        import httpx
        async def run():
            transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',10000))
            async with httpx.AsyncClient(transport=transport,base_url='http://test') as c:
                result=await c.post('/staff/tasks',json={'assignee':'Scout','title':'HTTP shared record','request':'Synthetic record only','source':'isolated-test'})
                self.assertEqual(result.status_code,200)
                tid=result.json()['task']['id']
                note=await c.post(f'/staff/tasks/{tid}/notes',json={'note':'Use the revised three-source scope.'})
                self.assertEqual(note.status_code,200)
                message=await c.post('/message',json={'message':'show task HTTP shared record','channel':'walkie'})
                self.assertEqual(message.json()['task']['id'],tid)
                board=await c.get('/staff/tasks/board',params={'task':tid})
                self.assertEqual(board.status_code,200)
                self.assertIn('revised three-source',board.text)
                bad=await c.post(f'/staff/tasks/{tid}/complete',json={'result':'text','status':'unknown'})
                self.assertEqual(bad.status_code,422)
        asyncio.run(run())

    def test_timeout_stops_worker(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            r.execute_worker([sys.executable,'-c','import time; time.sleep(15)'],dict(os.environ),1)

if __name__=='__main__': unittest.main()
