"""Shared mutation reservation. No timeout expiry, reset or send capability."""
SCHEMA='''CREATE TABLE IF NOT EXISTS email_mailbox_admission (
 mailbox TEXT PRIMARY KEY CHECK(mailbox='william'),operation_key TEXT NOT NULL UNIQUE,
 claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);'''
class MailboxHeld(RuntimeError):pass
def claim(connection,operation_key):
    if not connection.in_transaction:raise ValueError('Existing write transaction required')
    if not isinstance(operation_key,str) or not operation_key or len(operation_key)>200:raise ValueError('Bounded operation identity required')
    if connection.execute("SELECT 1 FROM email_mailbox_admission WHERE mailbox='william'").fetchone():raise MailboxHeld('An earlier mailbox mutation is active or unconfirmed; reconcile before another mutation')
    connection.execute("INSERT INTO email_mailbox_admission(mailbox,operation_key) VALUES('william',?)",(operation_key,))
def release(connection,operation_key):
    if not connection.in_transaction:raise ValueError('Existing write transaction required')
    if connection.execute("DELETE FROM email_mailbox_admission WHERE mailbox='william' AND operation_key=?",(operation_key,)).rowcount!=1:raise MailboxHeld('Mailbox reservation changed; preserve uncertainty')
