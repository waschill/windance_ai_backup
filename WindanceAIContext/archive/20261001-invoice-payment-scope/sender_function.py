def get_report() -> str:
    # Execute on HERALD so the Odoo credential remains only in Agent Harness.
    # Base64 avoids SSH/shell quoting changes to this read-only query.
    program = """import sys
sys.path.insert(0, '/Users/herald/services/agent-harness')
from agent_harness import odoo_unpaid_customer_invoices
report, kind, source = odoo_unpaid_customer_invoices(
    'Ledger daily report: show unpaid invoice details including invoice numbers and due dates.', limit=1000
)
if kind != 'deterministic' or source != 'odoo-unpaid-invoices':
    raise RuntimeError('Odoo unpaid invoice query failed; report withheld.')
print(report)
"""
    encoded = base64.b64encode(program.encode("utf-8")).decode("ascii")
    remote_command = (
        f"/Users/herald/.hermes/hermes-agent/venv/bin/python -c "
        f"\"import base64; exec(base64.b64decode('{encoded}'))\""
    )
    result = subprocess.run(
        ["ssh", "HERALD", remote_command],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown remote error").strip()
        raise RuntimeError(f"Ledger could not complete the read-only Odoo check: {detail[:700]}")
    report = result.stdout.strip()
    if not report:
        raise RuntimeError("Ledger received an empty Odoo report.")
    return "Ledger — Daily Unpaid Invoice Report\n\n" + report
