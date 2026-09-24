import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import supervisor as mod
import remote_ops

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.t = 10000
        self.calls = []
        def transport(host, cmd, payload=None, timeout=None):
            self.calls.append((host,cmd,payload))
            if cmd[0]=='prepare':
                return {'action':payload['action'],'incident':payload['incident'],'created':time.time(),'expires':time.time()+900}
            if cmd[0]=='review':
                return {'reviewer':'Claude','proposal_sha256':payload['proposal_sha256'],'decision':'approve','reason':'fixture approved'}
            if cmd[0] == 'recover':
                return {'performed':True}
            if cmd[0] == 'notify':
                return {'status':'delivered'}
            return {'host':host,'checks':{'harness':True}}
        self.s = mod.Supervisor(self.temp.name,transport,lambda:self.t)
        self.review=patch.object(mod.review_gate,'codex_review',side_effect=lambda root,p:{'reviewer':'Codex','proposal_sha256':mod.review_gate.digest(p),'decision':'approve','reason':'fixture approved'})
        self.review.start()
        self.snapshot = {'checks':{'harness':False}}
    def tearDown(self):
        self.review.stop()
        self.s.c.close()
        self.temp.cleanup()
    def sample(self,ok=False,key='HERALD:harness'):
        self.s.observe(key,ok,self.snapshot)
        self.t += 120
    def incident(self):
        return dict(self.s.c.execute('SELECT * FROM incidents ORDER BY opened DESC LIMIT 1').fetchone())
    def test_three_failures_one_repair_two_successes(self):
        self.sample(); self.sample()
        self.assertEqual(self.calls,[])
        self.sample()
        self.assertEqual(self.incident()['status'],'verifying')
        self.assertEqual(sum(c[1][0]=='recover' for c in self.calls),1)
        self.sample(True)
        self.assertEqual(self.incident()['status'],'verifying')
        self.sample(True)
        self.assertEqual(self.incident()['status'],'resolved')
    def test_timeout_never_repeats_mutation(self):
        original=self.s.transport
        def uncertain(*args,**kwargs):
            if args[1][0]=='recover': raise TimeoutError()
            return original(*args,**kwargs)
        self.s.transport = uncertain
        for _ in range(8): self.sample()
        self.assertEqual(self.incident()['attempts'],1)
        self.assertEqual(self.incident()['status'],'held')
    def test_flapping_circuit_breaker(self):
        for _ in range(3): self.sample()
        self.sample(True); self.sample(True)
        for _ in range(3): self.sample()
        self.assertEqual(self.incident()['status'],'escalated')
        self.assertEqual(sum(c[1][0]=='recover' for c in self.calls),1)
    def test_long_gap_resets_evidence(self):
        self.sample(); self.sample(); self.t += 2000; self.sample()
        self.assertEqual(self.calls,[])
    def test_dependency_failure_cannot_restart_workers(self):
        for _ in range(3): self.sample(key='HERALD:staff_progress')
        self.assertEqual(self.incident()['attempts'],0)
    def test_no_action_for_unknown_or_report(self):
        for _ in range(3): self.sample(key='SAL:youtube_delivery')
        self.assertEqual(self.calls,[])
        self.assertEqual(self.incident()['status'],'escalated')
    def test_pause_is_read_only(self):
        (Path(self.temp.name)/'PAUSED').write_text('maintenance')
        self.s.cycle()
        self.assertFalse(any(c[1][0] in ('recover','notify') for c in self.calls))
        self.assertEqual(self.s.c.execute('SELECT count(*) FROM checks').fetchone()[0],0)
    def test_notice_is_idempotent(self):
        self.s.notice('x','y','hello'); self.s.notice('x','y','hello')
        self.s.flush_notices(); self.s.flush_notices()
        self.assertEqual(sum(c[1][0]=='notify' for c in self.calls),1)
    def test_disagreement_never_executes(self):
        self.review.stop()
        with patch.object(mod.review_gate,'codex_review',side_effect=lambda root,p:{'reviewer':'Codex','proposal_sha256':mod.review_gate.digest(p),'decision':'reject','reason':'insufficient evidence'}):
            for _ in range(8): self.sample()
        self.assertEqual(self.incident()['status'],'held')
        self.assertEqual(self.incident()['attempts'],0)
        self.assertFalse(any(c[1][0] in ('review','recover') for c in self.calls))
    def test_interrupted_review_is_held(self):
        for _ in range(3): self.sample()
        with self.s.c: self.s.c.execute("UPDATE incidents SET status='reviewing'")
        self.calls.clear()
        self.s.cycle()
        self.assertEqual(self.incident()['status'],'held')
        self.assertFalse(any(c[1][0] in ('prepare','review','recover') for c in self.calls))
    def test_codex_daily_cap(self):
        for key in ('SAL:youtube_delivery','SAL:outbox','HERALD:connection'):
            for _ in range(3): self.sample(key=key)
        with patch.object(self.s,'diagnose',return_value={'summary':'unknown','next_step':'inspect'}) as diag:
            for _ in range(4): self.s.escalate({})
            self.assertEqual(diag.call_count,2)
    def test_recovery_can_be_observed_without_claiming_repair(self):
        for _ in range(3): self.sample(key='SAL:outbox')
        self.sample(True,key='SAL:outbox'); self.sample(True,key='SAL:outbox')
        self.assertEqual(self.incident()['attempts'],0)
        self.assertEqual(self.incident()['status'],'resolved')

class RemoteTests(unittest.TestCase):
    def test_unknown_action_fails_closed(self):
        with self.assertRaises(ValueError): remote_ops.recover('delete_database')
    def test_bare_action_has_no_approval(self):
        with patch.object(remote_ops,'HERALD',True):
            with self.assertRaises(ValueError): remote_ops.recover('restart_harness')
    def test_notification_reserved_never_requeues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            remote_ops.atomic(root/'notifications'/'abc.json',{'status':'reserved'})
            with patch.object(remote_ops,'HERALD',False),patch.object(remote_ops,'ROOT',root),patch.object(remote_ops,'HOME',root):
                self.assertEqual(remote_ops.notify({'key':'abc','text':'test'})['status'],'awaiting_receipt')
                self.assertFalse((root/'.local/share/windance-imessage-outbox/queue').exists())
    def test_notification_path_rejected(self):
        with patch.object(remote_ops,'HERALD',False):
            with self.assertRaises(ValueError): remote_ops.notify({'key':'../bad','text':'x'})

if __name__ == '__main__': unittest.main()
