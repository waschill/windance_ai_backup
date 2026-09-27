import asyncio
import datetime as dt
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

tmp = tempfile.TemporaryDirectory()
os.environ['AGENT_HARNESS_DATA_DIR'] = tmp.name
os.environ['AGENT_HARNESS_LOG_DIR'] = tmp.name
import agent_harness as h
import report_context as r


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 9, 27, 7, 20, tzinfo=r.ZONE)

    def test_tomorrow_is_not_today(self):
        text = r.calendar_section([{'summary': 'Appointment', 'start': {'dateTime': '2026-09-28T13:45:00-06:00'}, 'end': {'dateTime': '2026-09-28T14:45:00-06:00'}}], self.now, 2)
        self.assertIn('Sunday, September 27, 2026', text)
        self.assertIn('No upcoming events found for today.', text)
        self.assertIn('Tomorrow — September 28, 2026', text)
        self.assertIn('13:45–14:45: Appointment', text)

    def test_utc_rollover(self):
        now = dt.datetime(2026, 9, 28, 1, tzinfo=dt.timezone.utc)
        text = r.calendar_section([{'summary': 'Evening', 'start': {'dateTime': '2026-09-28T02:00:00Z'}}], now, 2)
        self.assertIn('Today — September 27, 2026', text)
        self.assertIn('20:00: Evening', text)
        self.assertNotIn('Tomorrow', text)

    def test_dst_and_all_day(self):
        now = dt.datetime(2026, 11, 1, 0, tzinfo=r.ZONE)
        text = r.calendar_section([{'summary': 'Day', 'start': {'date': '2026-11-01'}}, {'summary': 'After change', 'start': {'dateTime': '2026-11-01T15:00:00Z'}}], now, 2)
        self.assertIn('All day: Day', text)
        self.assertIn('08:00: After change', text)

    def test_calendar_failure_does_not_claim_empty(self):
        text = r.calendar_section([], self.now, 2, 'Timeout')
        self.assertIn('could not be verified', text)
        self.assertNotIn('No upcoming', text)

    def test_real_commands_are_not_report_discussion(self):
        for text in ['daily briefing', 'Send a daily briefing at 7 AM', 'Create an appointment tomorrow at 2 PM', 'Exclude Some Creator from the YouTube report', 'ALD 1', 'undo email 1', 'Change the briefing schedule to 8 AM']:
            self.assertFalse(r.is_report_discussion(text), text)
        self.assertTrue(h.is_recurring_task_creation_request('Send a daily briefing at 7 AM'))
        self.assertFalse(h.is_recurring_task_creation_request('The daily briefing is listed for tomorrow'))

    def test_original_messages_bypass_all_action_routes(self):
        messages = [
            'Dude!!! The daily briefing is listed for September 28th and today is September 27th. What’s up with that?',
            'You sent me this report:\nDaily briefing:\n### Schedule\nDoctors appointment\nAlways delete 1\nNotice the date. Why does it cover the 28th?',
            'The event already exists! The error in that report is the problem.',
        ]
        def fail(*args, **kwargs):
            raise AssertionError('Operational path reached')
        blocked = ['request_approval', 'create_staff_task', 'summarize_email_for_william', 'upcoming_calendar', 'process_numbered_gmail_pin_decisions', 'task_continuity_reply']
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in blocked:
                stack.enter_context(patch.object(h, name, fail))
            stack.enter_context(patch.object(h, 'require_token', lambda *a: None))
            stack.enter_context(patch.object(h, 'audit', lambda *a: None))
            stack.enter_context(patch.object(h, 'model_reply', lambda *a: ('Report explanation', 'test', 'test')))
            for text in messages:
                result = asyncio.run(h.message(h.MessageIn(message=text, user='william', channel='test'), None, None))
                self.assertEqual(result['model'], 'report-followup:test')

    def test_snapshot_isolation_and_exact_content(self):
        r.save_report(vars(h), 'daily_briefing', 'Exact saved report', {'evidence': 'fixture'}, user='fixture-owner')
        self.assertEqual(r.recent_reports(vars(h), 'fixture-owner')[0]['content'], 'Exact saved report')
        self.assertEqual(r.recent_reports(vars(h), 'another-user'), [])

    def test_briefing_no_model_invents_date_and_email_verbatim(self):
        email = '1. ESCALATE — untouched: Synthetic fixture'
        with patch.object(r, 'review_briefing', return_value=(True, {'fixture': True})), patch.object(r, 'mountain_now', return_value=self.now), patch.object(h, 'upcoming_calendar', return_value=[]), patch.object(h, 'summarize_email_for_william', return_value=(email, 'test', 'test')), patch.object(h, 'model_reply', side_effect=AssertionError('No date inference allowed')):
            text, _, _ = h.daily_briefing()
        self.assertIn('September 27, 2026', text)
        self.assertTrue(text.endswith(email))
        self.assertEqual(r.recent_reports(vars(h), 'william', 'daily_briefing')[0]['content'], text)

    def test_followup_receives_history_without_generating_report(self):
        r.save_report(vars(h), 'daily_briefing', 'Historical fixture text', user='history-owner')
        seen = []
        def model(system, text, fallback):
            seen.append(system)
            return 'Explanation', 'test', 'test'
        with patch.object(h, 'model_reply', model):
            r.report_followup(vars(h), 'Why was my briefing wrong?', 'history-owner', 'test')
        self.assertIn('Historical fixture text', seen[0])
        self.assertIn('READ-ONLY', seen[0])

    def test_athena_rejection_withholds_report(self):
        with patch.object(r, 'review_briefing', return_value=(False, {'reason': 'fixture'})), patch.object(h, 'upcoming_calendar', return_value=[]), patch.object(h, 'summarize_email_for_william', return_value=('SECRET FIXTURE REPORT', 'test', 'test')), patch.object(h, 'audit'):
            text, _, model = h.daily_briefing()
        self.assertEqual(model, 'athena-withheld')
        self.assertNotIn('SECRET FIXTURE REPORT', text)

    def test_athena_receipt_and_date_backstop(self):
        import herald_inference
        content = r.calendar_section([], self.now, 2)
        with patch.object(herald_inference, 'infer', return_value=('{"verdict":"APPROVED","reason":"Valid"}', 'test', 'athena')):
            ok, receipt = r.review_briefing(vars(h), content, [], self.now)
            bad, _ = r.review_briefing(vars(h), content.replace('Sunday, September 27', 'Monday, September 28'), [], self.now)
        self.assertTrue(ok)
        self.assertEqual(len(receipt['sha256']), 64)
        self.assertFalse(bad)

    def test_oauth_failure_has_no_provider_fallback(self):
        import herald_inference
        with patch.object(herald_inference, 'infer', side_effect=RuntimeError('Unavailable')), patch.object(h, 'audit'):
            text, provider, model = h.model_reply('system', 'user', 'Unable to answer')
        self.assertEqual((text, provider, model), ('Unable to answer', 'openai-codex-unavailable', 'gpt-5.6-terra'))

    def test_wrong_provider_receipt_is_rejected(self):
        import herald_inference
        from types import SimpleNamespace
        with patch.object(herald_inference.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='{"reply":"hi","provider":"ollama","model":"gemma4:latest"}')):
            with self.assertRaises(RuntimeError):
                herald_inference.infer('system', 'user')

    def test_completion_guard_allows_identity_not_false_receipts(self):
        from request_execution import unverified_claim
        self.assertFalse(unverified_claim('I am Reacher. I help get things done.'))
        for text in ['Done.', 'All set!', 'I updated the schedule.', 'It is done.']:
            self.assertTrue(unverified_claim(text), text)


if __name__ == '__main__':
    unittest.main()
