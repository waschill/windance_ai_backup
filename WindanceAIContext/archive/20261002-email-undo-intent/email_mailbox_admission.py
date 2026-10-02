"""Shared mutation reservation. No timeout expiry, reset or send capability."""
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS email_mailbox_admission (
 mailbox TEXT PRIMARY KEY CHECK(mailbox='william'),operation_key TEXT NOT NULL UNIQUE,
 claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);'''
class MailboxHeld(RuntimeError):pass
def _has_hold(connection):
    if connection.execute("SELECT 1 FROM email_mailbox_admission WHERE mailbox='william'").fetchone():return True
    # Older journal revisions may predate the shared reservation table.
    for table in ('email_action_intents','email_approved_item_intents','email_undo_intents'):
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():
            if connection.execute('SELECT 1 FROM '+table+" WHERE state='unconfirmed' LIMIT 1").fetchone():return True
    return False
def is_held(connect):
    with closing(connect()) as connection:
        return _has_hold(connection)
def claim(connection,operation_key):
    if not connection.in_transaction:raise ValueError('Existing write transaction required')
    if not isinstance(operation_key,str) or not operation_key or len(operation_key)>200:raise ValueError('Bounded operation identity required')
    if _has_hold(connection):raise MailboxHeld('An earlier mailbox mutation is active or unconfirmed; reconcile before another mutation')
    connection.execute("INSERT INTO email_mailbox_admission(mailbox,operation_key) VALUES('william',?)",(operation_key,))
def release(connection,operation_key):
    if not connection.in_transaction:raise ValueError('Existing write transaction required')
    if connection.execute("DELETE FROM email_mailbox_admission WHERE mailbox='william' AND operation_key=?",(operation_key,)).rowcount!=1:raise MailboxHeld('Mailbox reservation changed; preserve uncertainty')
