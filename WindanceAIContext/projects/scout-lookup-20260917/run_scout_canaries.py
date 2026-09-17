"""Runs the deployed worker + QA path with isolated lifecycle/fault injection.

No production queue consumption, outbound delivery, or provider config changes.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, '/Users/herald/services/profile-staff-runner')
import profile_staff_runner as runner
from scout_research_policy import release_evidence

base = Path(__file__).resolve().parent
python = '/Users/herald/.hermes/hermes-agent/venv/bin/python'
original_execute = runner.execute_worker


def isolated_lifecycle(path, method='GET', payload=None, **kwargs):
    if not path.endswith('/start') or method != 'POST':
        raise RuntimeError('Unexpected canary lifecycle mutation')
    return {'canary': True}


runner.request = isolated_lifecycle
for mode in sys.argv[1:] or ['normal', 'api_search_down', 'all_down']:
    trace = base / (mode + '-tools.jsonl')
    def execute(command, env, timeout):
        env = {**env, 'SCOUT_CANARY_MODE': mode, 'SCOUT_CANARY_TRACE': str(trace)}
        completed = original_execute([python, str(base / 'canary_hermes.py'), *command[1:]], env, timeout)
        with (base / (mode + '-phases.jsonl')).open('a') as audit:
            audit.write(json.dumps({'profile': env.get('HERMES_PROFILE'),
                                    'exit_code': completed.returncode,
                                    'output': runner.clean_worker_output(completed.stdout or '')}) + '\n')
        return completed
    runner.execute_worker = execute
    if mode in ('api_search_down', 'all_down'):
        def failed_receipt(task):
            def fail(req, **kwargs):
                if mode == 'all_down' or req.full_url.startswith('https://api.github.com/'):
                    raise ConnectionError('Controlled canary official-fetch outage')
                return urllib.request.urlopen(req, **kwargs)
            receipt = release_evidence(task, fail)
            (base / (mode + '-retrieval.json')).write_text(json.dumps(receipt, indent=2))
            return receipt
        runner.release_evidence = failed_receipt
    else:
        runner.release_evidence = release_evidence
    task = {'id': 'isolated-scout-' + mode, 'assignee': 'Scout',
            'title': 'Look up the latest Hermes version',
            'request': 'Look up the latest stable Hermes Agent version from Nous Research. Give its release date and official release link.',
            'requester': 'Vega canary', 'channel': 'internal-canary'}
    print('START ' + mode, flush=True)
    start = time.monotonic()
    output, status = runner.run_task(task, 240)
    result = {'mode': mode, 'status': status, 'elapsed_seconds': round(time.monotonic()-start),
              'output': output}
    (base / (mode + '-result.json')).write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
