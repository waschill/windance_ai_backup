import io
import json
import unittest
import subprocess
from unittest.mock import patch

import profile_staff_runner as runner
import scout_research_policy as policy


def task(request='Look up the latest Hermes Agent version'):
    return {'id': 'canary-unit', 'assignee': 'Scout', 'title': request, 'request': request}


RELEASE = {'name': 'Hermes Agent v0.21.3 (v2026.9.14)', 'tag_name': 'v2026.9.14',
           'published_at': '2026-09-14T16:04:00Z', 'draft': False, 'prerelease': False,
           'html_url': 'https://github.com/NousResearch/hermes-agent/releases/tag/v2026.9.14'}


class PolicyTests(unittest.TestCase):
    def test_original_lookup_receives_review(self):
        self.assertTrue(runner.is_scout_research_task(task()))

    def test_lookup_variants(self):
        for text in ['What is the current Hermes version?', 'Verify latest Ollama release',
                     'Find newest software version', 'Look up the latest Hermes version']:
            with self.subTest(text=text):
                self.assertTrue(policy.software_version_lookup(task(text)))

    def test_broad_and_high_stakes_do_not_get_exception(self):
        for text in ['Research treatment efficacy and latest protocol version',
                     'Latest Hermes version security risks', 'Compare latest versions',
                     'Latest Hermes version and new features', 'Check latest version and upgrade impact']:
            with self.subTest(text=text):
                self.assertFalse(policy.software_version_lookup(task(text)))

    def test_correct_single_source_lookup_passes_gate(self):
        output = 'PASS\nHermes v0.21.3, September 14, 2026. ' + RELEASE['html_url']
        self.assertEqual(runner.enforce_scout_research_gate(task(), output, 'completed')[1], 'completed')

    def test_missing_answer_rejected(self):
        for output in ['PASS\nRead the docs.', 'PASS\nv0.21.3',
                       'PASS\nSee https://github.com/NousResearch/hermes-agent']:
            self.assertEqual(runner.enforce_scout_research_gate(task(), output, 'completed')[1], 'partial')

    def test_partial_not_promoted(self):
        self.assertEqual(runner.enforce_scout_research_gate(task(), 'PARTIAL\nNo access', 'partial')[1], 'partial')

    def test_medical_gate_preserved(self):
        t = task('Research treatment efficacy for horses')
        output = 'PASS\nhttps://example.com/a https://example.com/b https://example.com/c'
        self.assertEqual(runner.enforce_scout_research_gate(t, output, 'completed')[1], 'partial')

    def test_host_spoof_does_not_pass(self):
        for url in ['https://evil.example/nih.gov', 'https://nih.gov.evil.example/a',
                    'https://evil.example/?ref=doi.org']:
            self.assertFalse(policy.strong_source_url(url))
        self.assertTrue(policy.strong_source_url('https://pubmed.ncbi.nlm.nih.gov/123'))

    def test_api_receipt(self):
        receipt = policy.release_evidence(task(), lambda *a, **kw: io.BytesIO(json.dumps(RELEASE).encode()))
        self.assertTrue(receipt['github_latest'])
        self.assertEqual(receipt['source_url'], RELEASE['html_url'])

    def test_api_failure_falls_back_to_direct_latest_page(self):
        with patch.object(policy.urllib.request, 'urlopen'):
            calls = []
            def fetch(req, **kw):
                calls.append(req.full_url)
                if len(calls) == 1:
                    raise OSError('canary failure')
                page = io.BytesIO(('<title>Release Hermes Agent v0.21.3 (v2026.9.14) · '
                                  'NousResearch/hermes-agent · GitHub</title>'
                                  '<relative-time datetime="2026-09-14T16:04:14Z">').encode())
                page.geturl = lambda: RELEASE['html_url']
                return page
            receipt = policy.release_evidence(task(), fetch)
        self.assertTrue(receipt['github_latest'])
        self.assertEqual(receipt['retrieval_method'], 'direct_release_page')
        self.assertEqual(len(receipt['attempts']), 2)

    def test_all_api_failures_remain_unverified(self):
        def fail(*a, **kw):
            raise OSError('canary failure')
        receipt = policy.release_evidence(task(), fail)
        self.assertTrue(receipt['unverified'])
        self.assertEqual(len(receipt['attempts']), 2)
        self.assertNotIn('name', receipt)

    def test_prerelease_and_wrong_repo_rejected(self):
        for change in [{'prerelease': True}, {'html_url': 'https://evil.example/release'}, {'published_at': ''}]:
            record = {**RELEASE, **change}
            receipt = policy.release_evidence(task(), lambda *a, **kw: io.BytesIO(json.dumps(record).encode()))
            self.assertTrue(receipt['unverified'])

    def test_unrelated_product_never_uses_hermes(self):
        for query in ['Latest Hermes 3 model version', 'Latest Gemma model release',
                      'Latest AcmeCanary software version']:
            self.assertIsNone(policy.known_release_repo(task(query)))

    def test_receipt_mismatch_rejected(self):
        t = task()
        t['_official_release_evidence'] = {**RELEASE, 'source_url': RELEASE['html_url'],
                                         'api_url': 'https://api.github.com/repos/NousResearch/hermes-agent/releases/latest',
                                         'github_latest': True}
        output = 'PASS\nv0.21.2 ' + RELEASE['html_url']
        self.assertEqual(runner.enforce_scout_research_gate(t, output, 'completed')[1], 'partial')

    def test_prefixed_version_receipt_match_passes(self):
        t = task()
        t['_official_release_evidence'] = {**RELEASE, 'source_url': RELEASE['html_url'],
                                         'api_url': 'https://api.github.com/repos/NousResearch/hermes-agent/releases/latest',
                                         'github_latest': True}
        output = 'PASS\nThe latest release is **v0.21.3**. ' + RELEASE['html_url']
        self.assertEqual(runner.enforce_scout_research_gate(t, output, 'completed')[1], 'completed')

    def test_review_verdict_formats(self):
        for text in ['APPROVED\nEvidence matches', '**Verdict: PASS**\nEvidence matches', 'PASS']:
            self.assertTrue(policy.review_approved(text))
        for text in ['REJECTED\nExample: APPROVED', '**Verdict: PARTIAL**',
                     'Not APPROVED', 'PASS but unsupported', 'Discussion\nAPPROVED']:
            self.assertFalse(policy.review_approved(text))

    def test_blocker_status_normalized(self):
        self.assertEqual(policy.without_status('**BLOCKED**.\nNo source access'), 'No source access')
        self.assertEqual(policy.without_status('PARTIAL\nNo source access'), 'No source access')

    def test_failed_lookup_keeps_one_blocked_status(self):
        with patch.object(runner, 'effective_turn_limit', return_value=1), \
             patch.object(runner, 'request', return_value={}), \
             patch.object(runner, 'release_evidence', return_value=None), \
             patch.object(runner, 'execute_worker', return_value=subprocess.CompletedProcess([], 0, 'BLOCKED.\nSources unavailable')), \
             patch.object(runner, 'athena_review', return_value=(False, 'BLOCKED\nNot verified')), \
             patch.object(runner, 'revise_scout_report', return_value=('BLOCKED.\nSources unavailable', 'blocked')):
            output, status = runner.run_task(task(), 10)
        self.assertEqual(status, 'blocked')
        self.assertEqual(output.count('BLOCKED'), 1)
        self.assertNotIn('PARTIAL', output)

    def test_contract_reaches_worker(self):
        self.assertIn('Search failure is one failed route', runner.task_prompt(task()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
