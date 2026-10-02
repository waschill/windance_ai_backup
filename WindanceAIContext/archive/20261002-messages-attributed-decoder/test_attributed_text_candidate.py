"""Synthetic Foundation fixtures only; no Messages database access or sender."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import time

wheel = Path(sys.argv[1])
assert hashlib.sha256(wheel.read_bytes()).hexdigest() == '499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278'
sys.path.insert(0, str(wheel.resolve()))
from attributed_text_candidate import decode_text

cases = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
start = time.monotonic()
checks = 0
blobs = {}
for case in cases:
    blob = base64.b64decode(case['base64'], validate=True)
    blobs[case['name']] = blob
    assert decode_text(blob) == case['expected'], case['name']
    checks += 1
for name in ('embedded', 'metadata'):
    assert b'EXPECTED' in blobs[name]
    assert decode_text(blobs[name]) != 'EXPECTED'
    checks += 1
for bad in (b'', b'not an archive', b'x'*262145, None, 'string'):
    assert decode_text(bad) is None
    checks += 1
plain = blobs['plain']
for n in range(len(plain)):
    assert decode_text(plain[:n]) is None, ('truncated', n)
    checks += 1
for suffix in (b'garbage', plain):
    assert decode_text(plain+suffix) is None
    checks += 1
print(json.dumps({'status':'passed','checks':checks,'foundation_cases':len(cases),
    'elapsed_seconds':round(time.monotonic()-start,4),
    'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),
    'real_messages_read':0,'sends':0,'production_installs':0}))
