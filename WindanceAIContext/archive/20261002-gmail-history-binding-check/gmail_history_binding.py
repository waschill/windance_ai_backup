"""Refuse silent account changes or automatic adoption of unbound historical state."""
import hashlib
from contextlib import closing

SCHEMA="""CREATE TABLE IF NOT EXISTS gmail_history_binding (
 owner TEXT PRIMARY KEY CHECK(owner='william'), account_sha256 TEXT NOT NULL,
 bound_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"""
HISTORY_TABLES=('max_email_tracking','max_email_report_refs','max_email_report_consumed',
    'max_email_sender_rules','email_autonomy_actions','email_report_active','email_action_intents',
    'email_draft_recovery_evidence','email_approved_item_intents','email_approval_selections',
    'email_undo_intents','email_mailbox_admission')
class BindingHeld(PermissionError):pass

def bind_verified(connect,expected):
    """Call only after provider profile matched independently configured expectation.

    No repair/adoption/reset operation is exposed. Historical adoption requires
    separate reviewed evidence and migration, not an implicit first invocation.
    """
    if not isinstance(expected,str) or '@' not in expected:raise BindingHeld('Verified account required')
    digest=hashlib.sha256(expected.casefold().encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE');c.execute(SCHEMA)
        row=c.execute("SELECT account_sha256 FROM gmail_history_binding WHERE owner='william'").fetchone()
        if row:
            if row[0]!=digest:raise BindingHeld('Mailbox account changed; historical state requires reconciliation')
            c.commit();return
        present={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in HISTORY_TABLES:
            if table in present and c.execute('SELECT 1 FROM '+table+' LIMIT 1').fetchone():
                raise BindingHeld('Historical mailbox state has no account binding; reviewed migration required')
        if 'approvals' in present and c.execute("SELECT 1 FROM approvals WHERE action LIKE 'gmail%' LIMIT 1").fetchone():
            raise BindingHeld('Historical mailbox approvals require account reconciliation')
        c.execute("INSERT INTO gmail_history_binding(owner,account_sha256) VALUES('william',?)",(digest,));c.commit()
