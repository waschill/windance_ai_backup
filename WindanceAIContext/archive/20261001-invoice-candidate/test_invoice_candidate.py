"""Isolated synthetic checks: no application import, transport or business I/O."""
from __future__ import annotations
import ast
import argparse
import base64
import builtins
import contextlib
import datetime as dt
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parent
original_sender = json.loads((ROOT / 'sender-original.json').read_text(encoding='utf-8-sig'))['function']
candidate_sender = original_sender.replace('report, _kind, _source =', 'report, kind, source =')
candidate_sender = candidate_sender.replace('print(report)\n',
    "if kind != 'deterministic' or source != 'odoo-unpaid-invoices':\n"
    "    raise RuntimeError('Odoo unpaid invoice query failed; report withheld.')\nprint(report)\n")
assert candidate_sender != original_sender
(ROOT / 'sender_function.py').write_text(candidate_sender + '\n', encoding='utf-8')

def row(identity=1, currency='USD', partner=1, residual=100, total=100, name=None):
    return dict(id=identity, name=name or f'SYN-{identity}', partner_id=[partner, 'Synthetic Customer'],
                invoice_date='2026-09-01', invoice_date_due='2026-09-10', amount_total=total,
                amount_residual=residual, currency_id=[{'USD': 1, 'EUR': 2, 'KWD': 3}[currency], currency],
                payment_state='partial' if residual != total else 'not_paid')

class InvoiceTests(unittest.TestCase):
    def setUp(self):
        self.rows = [row()]
        self.calls = []
        def query(*args, **kwargs):
            self.calls.append((args, kwargs))
            if isinstance(self.rows, Exception):
                raise self.rows
            return self.rows
        namespace = {'dt': dt, 'odoo_execute_kw': query}
        exec(compile((ROOT / 'invoice_function.py').read_text(), 'invoice_candidate', 'exec'), namespace)
        self.report = namespace['odoo_unpaid_customer_invoices']

    def test_read_only_query_contract(self):
        self.report(limit=5000)
        args, kwargs = self.calls[0]
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(args[:2], ('account.move', 'search_read'))
        self.assertIn(['state', '=', 'posted'], args[2][0])
        self.assertIn(['move_type', '=', 'out_invoice'], args[2][0])
        self.assertIn(['amount_residual', '>', 0], args[2][0])
        self.assertEqual(args[3]['limit'], 1000)

    def test_separate_currency_balances(self):
        self.rows = [row(), row(2, 'EUR')]
        report, kind, _ = self.report()
        self.assertEqual(kind, 'deterministic')
        self.assertIn('EUR 100.00; USD 100.00', report)
        self.assertNotIn('200.00', report)
        self.assertIn('Invoice SYN-1', report)
        self.assertIn('Invoice SYN-2', report)

    def test_duplicate_invoice_names_do_not_mix_amounts(self):
        self.rows = [row(name='SAME'), row(2, partner=2, total=600, residual=30, name='SAME')]
        report, _, _ = self.report()
        self.assertIn('2 customers', report)
        self.assertIn('Invoice Total: USD 600.00, Remaining: USD 30.00', report)

    def test_exact_decimal_sum(self):
        self.rows = [row(residual=0.1), row(2, residual=0.2)]
        self.assertIn('balances by currency: USD 0.30.', self.report()[0])

    def test_fractional_precision_preserved(self):
        self.rows = [row(currency='KWD', residual=1.234)]
        self.assertIn('KWD 1.234', self.report()[0])

    def test_empty_success_is_distinct_from_error(self):
        self.rows = []
        self.assertEqual(self.report()[1], 'deterministic')
        self.assertIn('no posted customer invoices', self.report()[0])
        self.rows = RuntimeError('SYNTHETIC_PRIVATE_PAYLOAD')
        report, kind, _ = self.report()
        self.assertEqual(kind, 'odoo-error')
        self.assertNotIn('SYNTHETIC_PRIVATE_PAYLOAD', report)
        self.assertNotIn('no posted customer invoices', report)

    def test_malformed_rows_fail_closed(self):
        for change in [dict(currency_id=False), dict(amount_residual='NaN'),
                       dict(amount_total='Infinity'), dict(amount_residual=-1),
                       dict(invoice_date_due='bad-date'), dict(payment_state='paid')]:
            with self.subTest(change=change):
                self.rows = [dict(row(), **change)]
                self.assertEqual(self.report()[1], 'odoo-error')
        self.rows = [row(), row()]
        self.assertEqual(self.report()[1], 'odoo-error')

    def test_unknown_currency_never_defaults_to_dollars(self):
        self.rows = [dict(row(), currency_id=[5, ''])]
        self.assertEqual(self.report()[1], 'odoo-error')

    def test_missing_date_and_invoice_name(self):
        self.rows = [dict(row(), invoice_date_due=False, name=False)]
        report, kind, _ = self.report()
        self.assertEqual(kind, 'deterministic')
        self.assertIn('Invoice Odoo #1', report)
        self.assertIn('Due no due date', report)

    def test_effective_cap_warning_and_scope(self):
        report, _, _ = self.report(limit=0)
        self.assertIn('hit the 1-invoice read limit', report)
        self.assertIn('totals cover only the displayed records', report)

    def sender(self):
        # Execute the actual encoded query program with an in-memory import stub.
        # This cannot launch SSH, import Harness, or reach an Odoo endpoint.
        def run(argv, **kwargs):
            encoded = argv[-1].split("b64decode('", 1)[1].split("')", 1)[0]
            program = base64.b64decode(encoded).decode()
            self.assertEqual(kwargs['timeout'], 120)
            self.assertNotIn('post_nodered', program)
            real_import = builtins.__import__
            def import_stub(name, *args, **kw):
                if name == 'agent_harness':
                    return types.SimpleNamespace(odoo_unpaid_customer_invoices=self.report)
                if name == 'sys':
                    return types.SimpleNamespace(path=[])
                raise AssertionError('Unexpected remote import: ' + name)
            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout):
                    exec(program, {'__builtins__': dict(vars(builtins), __import__=import_stub)})
                return types.SimpleNamespace(returncode=0, stdout=stdout.getvalue(), stderr='')
            except RuntimeError as error:
                return types.SimpleNamespace(returncode=1, stdout='', stderr=str(error))
        namespace = {'base64': base64, 'subprocess': types.SimpleNamespace(run=run)}
        exec(candidate_sender, namespace)
        return namespace['get_report']()

    def test_sender_withholds_query_failure(self):
        self.rows = RuntimeError('SYNTHETIC_PRIVATE_PAYLOAD')
        with self.assertRaisesRegex(RuntimeError, 'report withheld') as raised:
            self.sender()
        self.assertNotIn('SYNTHETIC_PRIVATE_PAYLOAD', str(raised.exception))

    def test_sender_accepts_verified_empty_and_nonempty_results(self):
        self.assertIn('Invoice SYN-1', self.sender())
        self.rows = []
        self.assertIn('no posted customer invoices', self.sender())

    def run_main(self, send):
        sends, alerts = [], []
        class Parser:
            def add_argument(self, *args, **kwargs): pass
            def parse_args(self): return types.SimpleNamespace(send=send, print_only=not send)
        namespace = {'argparse': types.SimpleNamespace(ArgumentParser=Parser),
                     'sys': types.SimpleNamespace(stdout=io.StringIO()), 'get_report': self.sender,
                     'send_to_recipients': sends.append, 'alert_william': alerts.append}
        source = json.loads((ROOT / 'main-original.json').read_text(encoding='utf-8-sig'))['function']
        exec(source, namespace)
        with contextlib.redirect_stdout(io.StringIO()):
            code = namespace['main']()
        return code, sends, alerts

    def test_job_failure_never_sends_normal_report(self):
        self.rows = RuntimeError('SYNTHETIC_READ_FAILURE')
        code, sends, alerts = self.run_main(True)
        self.assertEqual(code, 1)
        self.assertEqual(sends, [])
        self.assertEqual(len(alerts), 1)  # Fake alert only; existing route preserved.

    def test_print_only_failure_has_no_notifications(self):
        self.rows = RuntimeError('SYNTHETIC_READ_FAILURE')
        self.assertEqual(self.run_main(False), (1, [], []))

    def test_success_routes_once_and_preview_does_not_send(self):
        code, sends, alerts = self.run_main(True)
        self.assertEqual((code, len(sends), len(alerts)), (0, 1, 0))
        self.assertEqual(self.run_main(False), (0, [], []))

if __name__ == '__main__':
    unittest.main(verbosity=2)
