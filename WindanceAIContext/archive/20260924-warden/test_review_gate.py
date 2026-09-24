import copy
import json
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import review_gate as gate

class ConsensusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        code=root/'remote_ops.py'; code.write_text('# fixture')
        self.snapshot={'checks':{'harness':False,'gateway':False,'runner':True},'harness':{'pid':10},'gateway':{'pid':0},'runner':{'pid':0}}
        self.ops=types.SimpleNamespace(ROOT=root,HERALD=True,__file__=str(code),LABELS={'harness':'test.harness','gateway':'test.gateway','runner':'test.runner'},
            probe=Mock(side_effect=lambda:copy.deepcopy(self.snapshot)),run=Mock(return_value=types.SimpleNamespace(returncode=0)))
        self.p=gate.prepare(self.ops,'restart_harness','INC-20260924-1234abcd','HERALD:harness')
        self.sha=gate.digest(self.p)
        self.folder=root/'reviews'/self.sha
        self.ops.run.reset_mock()
    def tearDown(self): self.tmp.cleanup()
    def approve(self,who,decision='approve',sha=None):
        gate.save(self.folder/(who.lower()+'.json'),{'reviewer':who,'proposal_sha256':sha or self.sha,'decision':decision,'reason':'test evidence'})
    def both(self): self.approve('Codex'); self.approve('Claude')
    def test_two_approvals_execute_only_once(self):
        self.both()
        self.assertTrue(gate.authorized_recovery(self.ops,self.sha)['performed'])
        with self.assertRaises(FileExistsError): gate.authorized_recovery(self.ops,self.sha)
        self.assertEqual(sum(c.args[0][1]=='kickstart' for c in self.ops.run.call_args_list),1)
    def test_missing_review_never_executes(self):
        self.approve('Codex')
        with self.assertRaises(FileNotFoundError): gate.authorized_recovery(self.ops,self.sha)
        self.ops.run.assert_not_called()
    def test_disagreement_never_executes(self):
        self.approve('Codex'); self.approve('Claude','reject')
        with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)
        self.ops.run.assert_not_called()
    def test_different_proposal_never_executes(self):
        self.approve('Codex'); self.approve('Claude',sha='0'*64)
        with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)
    def test_expired_approvals_never_execute(self):
        self.both()
        with patch.object(gate.time,'time',return_value=self.p['expires']):
            with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)
    def test_changed_executor_never_executes(self):
        self.both(); Path(self.ops.__file__).write_text('# changed')
        with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)
    def test_changed_process_never_executes(self):
        self.both(); self.snapshot['harness']['pid']=11
        with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)
    def test_healthy_service_is_not_restarted(self):
        self.both(); self.snapshot['checks']['harness']=True
        self.assertFalse(gate.authorized_recovery(self.ops,self.sha)['performed'])
        self.ops.run.assert_not_called()
    def test_timeout_reserves_review_without_retry(self):
        verdict={'reviewer':'Codex','proposal_sha256':self.sha,'decision':'approve','reason':'test'}
        with patch.object(gate,'execute_bounded',side_effect=RuntimeError('timeout')) as invoke:
            with self.assertRaises(RuntimeError): gate.claude_review(self.ops,{'proposal_sha256':self.sha,'codex':verdict})
            with self.assertRaises(FileExistsError): gate.claude_review(self.ops,{'proposal_sha256':self.sha,'codex':verdict})
            self.assertEqual(invoke.call_count,1)
    def test_running_gateway_is_never_restarted(self):
        self.snapshot['gateway']['pid']=55
        p=gate.prepare(self.ops,'start_gateway','INC-20260924-1234abcd','HERALD:gateway')
        self.p=p; self.sha=gate.digest(p); self.folder=self.ops.ROOT/'reviews'/self.sha; self.both()
        with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)

if __name__=='__main__': unittest.main()
