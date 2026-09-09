import os
import sys
import tempfile
import unittest
from unittest.mock import patch
temp=tempfile.TemporaryDirectory(prefix='windance-goal-controls-')
os.environ['HERMES_HOME']=temp.name
os.environ.pop('HERMES_PROFILE',None)
sys.path.insert(0,'/Users/herald/.hermes/hermes-agent')
from hermes_cli.goals import GoalManager

class Tests(unittest.TestCase):
    def test_budget_failure_and_persistence(self):
        m=GoalManager('budget-test');m.set('Test goal',max_turns=2)
        with patch('hermes_cli.goals.judge_goal',return_value=('continue','transport unavailable',False,None,True)):
            self.assertTrue(m.evaluate_after_turn('unfinished')['should_continue'])
            recovered=GoalManager('budget-test')
            self.assertEqual(recovered.state.turns_used,1)
            d=recovered.evaluate_after_turn('unfinished')
            self.assertEqual(d['status'],'paused')
            self.assertFalse(d['should_continue'])
    def test_blocked_is_not_done(self):
        m=GoalManager('blocked-test');m.set('Missing required input',max_turns=2)
        with patch('hermes_cli.goals.judge_goal',return_value=('blocked','Need operator choice',False,None,False)):
            self.assertEqual(m.evaluate_after_turn('Cannot proceed')['status'],'paused')
            self.assertNotEqual(m.state.status,'done')
    def test_pause_does_not_spend(self):
        m=GoalManager('pause-test');m.set('Test pause',max_turns=2);m.pause()
        with patch('hermes_cli.goals.judge_goal',side_effect=AssertionError('Paused goal called a model')):
            self.assertFalse(m.evaluate_after_turn('text')['should_continue'])
            self.assertEqual(m.state.turns_used,0)
        m.resume(reset_budget=False)
        self.assertTrue(m.is_active())
if __name__=='__main__': unittest.main()
