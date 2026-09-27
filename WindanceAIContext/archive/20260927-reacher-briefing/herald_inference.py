"""Bounded subprocess boundary keeps Hermes profile state out of the Harness."""
import json
import subprocess
from pathlib import Path


def infer(system, user, profile='herald'):
    result = subprocess.run(
        ['/Users/herald/.hermes/hermes-agent/venv/bin/python',
         str(Path(__file__).with_name('profile_inference.py'))],
        input=json.dumps({'system': system, 'user': user, 'profile': profile}),
        text=True, capture_output=True, timeout=95,
    )
    if result.returncode:
        raise RuntimeError('Profile inference unavailable')
    data = json.loads(result.stdout)
    if profile == 'herald' and (data.get('provider'), data.get('model')) != ('openai-codex', 'gpt-5.6-terra'):
        raise RuntimeError('Unexpected Herald provider receipt')
    if not data.get('reply'):
        raise RuntimeError('Missing inference receipt')
    return data['reply'], data['provider'], data['model']
