import copy
import hashlib
import json
import tempfile
import time
import types
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import review_gate as gate

class ConsensusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        code=root/'remote_ops.py'; code.write_text('# fixture')
        wrapper=root/'claude_review.py'; wrapper.write_text('# pinned wrapper fixture')
        (root/'config.json').write_text(json.dumps({'claude_wrapper_sha256':hashlib.sha256(wrapper.read_bytes()).hexdigest()}))
        self.wrapper=patch.object(gate,'CLAUDE_WRAPPER',wrapper); self.wrapper.start()
        self.snapshot={'checks':{'harness':False,'gateway':False,'runner':True},'harness':{'pid':10},'gateway':{'pid':0},'runner':{'pid':0}}
        self.ops=types.SimpleNamespace(ROOT=root,HERALD=True,__file__=str(code),LABELS={'harness':'test.harness','gateway':'test.gateway','runner':'test.runner'},
            probe=Mock(side_effect=lambda:copy.deepcopy(self.snapshot)),run=Mock(return_value=types.SimpleNamespace(returncode=0,stdout='\tpath = '+str(code)+'\n\tprogram = /bin/sleep\n\tdomain = fixture')))
        self.p=gate.prepare(self.ops,'restart_harness','INC-20260924-1234abcd','HERALD:harness')
        self.sha=gate.digest(self.p)
        self.folder=root/'reviews'/self.sha
        self.ops.run.reset_mock()
    def tearDown(self): self.wrapper.stop(); self.tmp.cleanup()
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
    def test_changed_service_config_never_executes(self):
        self.both()
        self.ops.run.return_value.stdout+='\n'
        original=gate.service_fingerprint(self.ops,self.p['command'][-1])
        with patch.object(gate,'service_fingerprint',return_value={**original,'plist_sha256':'changed'}):
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
    def test_changed_reviewer_wrapper_never_executes(self):
        self.both(); gate.CLAUDE_WRAPPER.write_text('# different reviewer')
        with self.assertRaises(ValueError): gate.authorized_recovery(self.ops,self.sha)
    def test_key_action_mismatch_rejected(self):
        with self.assertRaises(ValueError): gate.prepare(self.ops,'restart_harness','INC-20260924-1234abcd','HERALD:gateway')
    def test_tampered_proposal_rejected(self):
        changed={**self.p,'action':'start_gateway'}
        gate.save(self.folder/'proposal.json',changed)
        with self.assertRaises(ValueError): gate.load_proposal(self.ops,self.sha)
    def test_strict_claude_output_and_session_receipt(self):
        verdict={'reviewer':'Claude','proposal_sha256':self.sha,'decision':'approve','reason':'fixture'}
        content=json.dumps(verdict)
        value,sid=gate.parse_claude(content,self.p,'Warning: fixture\n\nsession_id: 20260924_144117_b3af41\n')
        self.assertEqual(value,verdict)
        with self.assertRaises(ValueError): gate.parse_claude(content,self.p,'session_id: 20260924_144117_b3af41\nsession_id: 20260924_144117_b3af41\n')
        with self.assertRaises(ValueError): gate.parse_claude('session_id: 20260924_144117_b3af41\n'+content,self.p,'')
        with self.assertRaises(ValueError): gate.parse_claude('session_id: 20260924_144117_b3af41\n'+content,self.p,'session_id: 20260924_152508_33977e\n')
        for form in (content,'```json\n'+content+'\n```','```\n'+content+'\n```'):
            value,sid=gate.parse_claude('\nsession_id: 20260924_144117_b3af41\n'+form,self.p)
            self.assertEqual(value,verdict)
            self.assertEqual(sid,'20260924_144117_b3af41')
        for form in ('',content,'session_id: 20260924_144117_b3af41\nHere is my assessment: '+content,
                     'session_id: 20260924_144117_b3af41\nnot JSON',
                     'session_id: 20260924_144117_b3af41\n'+json.dumps({**verdict,'execute':'anything'})):
            with self.assertRaises(ValueError): gate.parse_claude(form,self.p)
    def test_live_launchctl_layout_fixtures(self):
        fixtures=json.loads((Path(__file__).parent/'launchctl-fixtures.json').read_text())
        for value in fixtures.values():
            # Preserve live structure while replacing only the config path with this test file.
            import re
            rendered=re.sub(r'(?m)^\tpath = .+$','\tpath = '+self.ops.__file__,value)
            self.ops.run.return_value.stdout=rendered
            a=gate.service_fingerprint(self.ops,'fixture')
            self.ops.run.return_value.stdout=re.sub(r'(?m)^\t(pid|runs|state|active count) = .+$',r'\t\1 = changed',rendered)
            self.assertEqual(a,gate.service_fingerprint(self.ops,'fixture'))
    def test_reviewer_gets_executable_and_current_authority(self):
        self.assertEqual(self.p['service_fingerprint']['executable'],'/bin/sleep')
        prompt=gate.review_prompt(self.p,'Codex')
        self.assertIn('Current direct operator authorization from William',prompt)
        self.assertIn('only if both agree',prompt)
    def test_claude_pipeline_parses_separate_streams_then_audits(self):
        codex={'reviewer':'Codex','proposal_sha256':self.sha,'decision':'approve','reason':'fixture'}
        claude={**codex,'reviewer':'Claude'}
        sid='20260924_152508_33977e'
        with patch.object(gate,'execute_bounded',return_value=('Human warning, not JSON','\nsession_id: '+sid+'\n')),patch.object(gate,'canonical_claude_response',return_value=json.dumps(claude)),patch.object(gate,'audit_claude_session',return_value={'session_id':sid,'model':'anthropic/claude-opus-5','provider':'openrouter','tools':[]}) as audit:
            self.assertEqual(gate.claude_review(self.ops,{'proposal_sha256':self.sha,'codex':codex}),claude)
            audit.assert_called_once_with(sid)
        self.assertEqual(json.loads((self.folder/'claude-session.json').read_text())['session_id'],sid)
        self.assertEqual(json.loads((self.folder/'claude.json').read_text()),claude)
    def test_canonical_response_must_belong_to_exact_proposal(self):
        root=Path(self.tmp.name)
        path=root/'.hermes/profiles/claude/state.db'; path.parent.mkdir(parents=True)
        c=sqlite3.connect(path)
        c.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY,session_id TEXT,role TEXT,content TEXT)')
        verdict={'reviewer':'Claude','proposal_sha256':self.sha,'decision':'approve','reason':'x'*2034}
        c.execute('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',('fixture','user','Quoted hash only '+self.sha))
        c.execute('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',('fixture','assistant',json.dumps(verdict))); c.commit()
        with patch.object(gate.Path,'home',return_value=root):
            with self.assertRaises(ValueError): gate.canonical_claude_response('fixture',self.p)
            c.execute('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',('fixture','user',gate.review_prompt(self.p,'Claude')))
            c.execute('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',('fixture','assistant',json.dumps(verdict))); c.commit()
            response=gate.canonical_claude_response('fixture',self.p)
            self.assertEqual(gate.validate_verdict(json.loads(response),self.p,'Claude'),verdict)
            c.execute('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',('fixture','user','Later unrelated follow-up'))
            for later in ('Unrelated prose',json.dumps({**verdict,'proposal_sha256':'0'*64})):
                c.execute('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',('fixture','assistant',later)); c.commit()
                self.assertEqual(gate.canonical_claude_response('fixture',self.p),response)
        c.close()
    def test_claude_identity_and_tools_checked_against_session(self):
        root=Path(self.tmp.name)
        path=root/'.hermes/profiles/claude/state.db'; path.parent.mkdir(parents=True)
        c=sqlite3.connect(path)
        c.executescript('CREATE TABLE sessions(id TEXT,model TEXT,billing_provider TEXT); CREATE TABLE messages(session_id TEXT,role TEXT,tool_name TEXT);')
        c.execute('INSERT INTO sessions VALUES(?,?,?)',('fixture','anthropic/claude-opus-5','openrouter')); c.commit()
        with patch.object(gate.Path,'home',return_value=root):
            self.assertEqual(gate.audit_claude_session('fixture')['tools'],[])
            c.execute('INSERT INTO messages VALUES(?,?,?)',('fixture','tool','memory')); c.commit()
            with self.assertRaises(ValueError): gate.audit_claude_session('fixture')
        c.close()

if __name__=='__main__': unittest.main()
