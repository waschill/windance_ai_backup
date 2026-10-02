"""Actual SQLite report/reference/rule integration with synthetic mailbox effects."""
import ast, datetime as dt, hashlib, json, os, re, sqlite3, sys, tempfile, uuid
from email.utils import parseaddr
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
rule_command = sys.argv[2] if len(sys.argv) > 2 else 'always delete'
assert rule_command in ('always delete', 'notify delete')
sys.path.insert(0, str(root))
manifest = json.loads((root / 'manifest.json').read_text())
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == v for n, v in manifest.items())
source = (root / 'agent_harness.candidate.private.py').read_text()
names = {'db', 'ClosingConnection', 'seed_memories', 'audit', 'prepare_gmail_report_reply_actions',
         'numbers_after_keywords', 'save_email_report_refs', 'latest_email_ref_map',
         'consume_latest_email_ref_map', 'upsert_email_sender_rule', 'sender_address',
         'short_sender', 'compact_subject'}
nodes = [n for n in ast.parse(source).body if getattr(n, 'name', '') in names]
assert len(nodes) == len(names)
results = []
for mode in ('normal', 'lost', 'empty_latest', 'invalid_reference'):
    with tempfile.TemporaryDirectory() as folder:
        effects = []
        def trash(mid):
            effects.append(mid)
            if mode == 'lost':
                raise TimeoutError('PRIVATE_PROVIDER_SENTINEL')
            return {'trashed': True, 'id': mid}
        def forbidden(*args, **kwargs):
            raise AssertionError('Unexpected model/approval path')
        ns = dict(Any=Any, sqlite3=sqlite3, os=os, DB_FILE=Path(folder)/'fixture.db',
                  ensure_dirs=lambda: None, dt=dt, uuid=uuid, re=re, json=json,
                  now=lambda: dt.datetime.now(dt.UTC).isoformat(), parseaddr=parseaddr,
                  require_william_mailbox=lambda: None, gmail_delete_message=trash,
                  compose_numbered_email_draft=forbidden, request_approval=forbidden)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-rule-storage>', 'exec'), ns)
        rows = [(i, 'test', {'id': f'synthetic-{i}', 'from': f'Person {i} <person{i}@example.invalid>',
                            'subject': 'Synthetic fixture'}) for i in (1, 2)]
        ns['save_email_report_refs']('first', rows)
        assert set(ns['latest_email_ref_map']()) == {1, 2}
        if mode == 'empty_latest':
            ns['save_email_report_refs']('empty', [])
        command = rule_command + (' 1 and 2' if mode != 'invalid_reference' else ' 1 and 9')
        response = ns['prepare_gmail_report_reply_actions'](command)
        assert 'PRIVATE_PROVIDER_SENTINEL' not in repr(response)
        with ns['db']() as conn:
            rule_count = conn.execute('SELECT count(*) FROM max_email_sender_rules').fetchone()[0]
        if mode == 'normal':
            assert len(effects) == rule_count == 2
            assert set(ns['latest_email_ref_map']()) == {1, 2}
            ns['prepare_gmail_report_reply_actions'](command)
            assert len(effects) == 2
            ns['save_email_report_refs']('later', rows)
            ns['prepare_gmail_report_reply_actions'](command)
            assert len(effects) == 4
        elif mode == 'lost':
            assert len(effects) == 1
            # Must stop the whole command after uncertainty, including local rules.
            assert rule_count == 1, f'Unexpected later sender rule persisted: {rule_count}'
            assert response[2] == 'gmail-summary-held'
            ns['prepare_gmail_report_reply_actions'](command)
            assert len(effects) == 1
        else:
            assert len(effects) == rule_count == 0
            assert response[2] == 'gmail-report-invalid'
        results.append({'case': mode, 'synthetic_effects': len(effects), 'passed': True})
print(json.dumps({'command': rule_command, 'candidate_sha256': manifest['agent_harness.candidate.private.py'],
                  'cases': results, 'actual_mailbox_calls': 0,
                  'limits': 'Owner check intercepted; no request transport or concurrency proof.'}))
