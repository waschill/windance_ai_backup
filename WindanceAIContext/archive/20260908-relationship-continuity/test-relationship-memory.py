"""Exercise native persistence in disposable isolated homes, without model calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = '/Users/herald/.hermes/hermes-agent'
sys.path.insert(0, REPO)
from hermes_constants import set_hermes_home_override, reset_hermes_home_override
from tools.memory_tool import MemoryStore, memory_tool


with tempfile.TemporaryDirectory(prefix='windance-memory-test-') as tmp:
    a, b, gated = [Path(tmp) / n for n in ('a', 'b', 'gated')]
    for p in (a, b, gated):
        p.mkdir(mode=0o700)
        (p / 'config.yaml').write_text('memory:\n  memory_enabled: true\n  user_profile_enabled: true\n  write_approval: ' + ('true' if p == gated else 'false') + '\n')
    token = set_hermes_home_override(a)
    try:
        store = MemoryStore()
        store.load_from_disk()
        entry = '[Synthetic test, 2026-09-08] The test user prefers brief answers.'
        result = json.loads(memory_tool(action='add', target='user', content=entry, store=store))
        assert result.get('success') and not result.get('staged'), result
        code = '''import sys
sys.path.insert(0, sys.argv[1])
from hermes_constants import set_hermes_home_override
set_hermes_home_override(sys.argv[2])
from tools.memory_tool import MemoryStore
s=MemoryStore(); s.load_from_disk()
assert 'prefers brief answers' in s.format_for_system_prompt('user')
print('fresh_process_recall: PASS')
'''
        subprocess.run([sys.executable, '-c', code, REPO, str(a)], check=True)
        token_b = set_hermes_home_override(b)
        try:
            other = MemoryStore(); other.load_from_disk()
            assert 'prefers brief answers' not in (other.format_for_system_prompt('user') or '')
        finally:
            reset_hermes_home_override(token_b)
        print('cross_profile_isolation: PASS')
        result = json.loads(memory_tool(action='replace', target='user', old_text='prefers brief answers',
                            content='[Synthetic correction] The test user prefers detailed answers.', store=store))
        assert result.get('success') and not result.get('staged'), result
        fresh = MemoryStore(); fresh.load_from_disk()
        block = fresh.format_for_system_prompt('user')
        assert 'prefers detailed answers' in block and 'prefers brief answers' not in block
        print('correction_replaces_stale_preference: PASS')
        result = json.loads(memory_tool(action='remove', target='user', old_text='prefers detailed answers', store=fresh))
        assert result.get('success') and not result.get('staged'), result
        cleared = MemoryStore(); cleared.load_from_disk()
        assert 'prefers detailed answers' not in (cleared.format_for_system_prompt('user') or '')
        print('forget_removes_active_memory: PASS')
        too_big = json.loads(memory_tool(action='add', target='user', content='x' * 2000, store=cleared))
        assert too_big.get('success') is False
        print('bounded_memory_budget: PASS')
        token_g = set_hermes_home_override(gated)
        try:
            s = MemoryStore(); s.load_from_disk()
            pending = json.loads(memory_tool(action='add', target='user', content=entry, store=s))
            assert pending.get('staged') and pending.get('pending_id'), pending
            verify = MemoryStore(); verify.load_from_disk()
            assert entry not in (verify.format_for_system_prompt('user') or '')
            print('approval_gate_stages_without_persisting: PASS')
        finally:
            reset_hermes_home_override(token_g)
    finally:
        reset_hermes_home_override(token)
