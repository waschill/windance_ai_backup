"""Run on SAL: extract only enqueue and exercise private temporary directories."""
from __future__ import annotations
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

source = Path('/Users/zuzu/bin/send_imessage_payload.py').read_text()
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'enqueue')
namespace = dict(Path=Path, fcntl=fcntl, hashlib=hashlib, json=json, os=os, uuid=uuid)
exec(compile(ast.Module(body=[function], type_ignores=[]), '<extracted-enqueue>', 'exec'), namespace)
checks = []
with tempfile.TemporaryDirectory(prefix='windance-outbox-isolation-') as temporary:
    root = Path(temporary)
    queue, results = root / 'queue', root / 'results'
    namespace.update(ROOT=root, QUEUE=queue, RESULTS=results)
    enqueue = namespace['enqueue']
    payload = {'to': '+12025550123', 'text': 'Synthetic training fixture', 'sms': False}
    key = 'training-Shawn-2026-09-30'
    result, retained = enqueue(payload, key)
    assert retained and len(list(queue.glob('*.json'))) == 1
    assert enqueue(payload, key)[0] == result and len(list(queue.glob('*.json'))) == 1
    checks.append('duplicate trigger retains one queue identity')
    try:
        enqueue(dict(payload, text='Changed fixture'), key)
    except ValueError:
        pass
    else:
        raise AssertionError('changed content was accepted')
    checks.append('changed content under same key held')
    queued = queue / result.name
    queued.unlink()
    for folder in ('inflight', 'uncertain'):
        marker = root / folder / result.name
        marker.parent.mkdir()
        marker.write_text('{}')
        enqueue(payload, key)
        assert not queued.exists()
        marker.unlink()
        checks.append(folder + ' marker prevents requeue')
    result.write_text('{"ok":true,"synthetic":true}')
    enqueue(payload, key)
    assert not queued.exists() and json.loads(result.read_text())['synthetic']
    checks.append('retained receipt prevents requeue')
    result.unlink()
    enqueue(payload, key)
    assert queued.exists()
    checks.append('claim without queue receipt or uncertainty recreates queue')
print(json.dumps({'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'checks': checks, 'passed': len(checks), 'actual_sends': 0,
                  'live_outbox_access': False, 'daemon_started': False}))
