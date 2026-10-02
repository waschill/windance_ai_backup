"""Staged SAL Messages intake policy; does not send, advance cursors or authenticate HTTP."""
import re


def normalize_sender(sender):
    if not isinstance(sender,str):return ''
    value=sender.strip()
    # Current private allowlist uses telephone handles. Email enrollment is a
    # separate explicit policy change; never convert an email into phone digits.
    if not re.fullmatch(r'\+?[0-9 ()-]+',value):return ''
    digits=re.sub(r'[^0-9]','',value)
    return digits if 7 <= len(digits) <= 15 else ''


def pending_messages(connection, after):
    """Return every eligible row, including rejected rows for caller cursor handling.

    Style45 is the observed current direct-chat shape, not a universal Apple
    schema guarantee. Unknown, missing or ambiguous metadata fails closed.
    """
    return list(connection.execute('''
      SELECT m.ROWID,m.text,h.id,
        CASE WHEN
          (SELECT count(*) FROM chat_message_join j WHERE j.message_id=m.ROWID)=1
          AND EXISTS (
            SELECT 1 FROM chat_message_join j JOIN chat c ON c.ROWID=j.chat_id
            WHERE j.message_id=m.ROWID AND c.style=45 AND coalesce(c.room_name,'')=''
              AND (SELECT count(DISTINCT q.handle_id) FROM chat_handle_join q WHERE q.chat_id=c.ROWID)=1
              AND EXISTS (SELECT 1 FROM chat_handle_join q WHERE q.chat_id=c.ROWID AND q.handle_id=m.handle_id)
          ) THEN 1 ELSE 0 END AS direct_verified
      FROM message m JOIN handle h ON m.handle_id=h.ROWID
      WHERE m.is_from_me=0 AND m.text IS NOT NULL AND length(trim(m.text))>0 AND m.ROWID>?
      ORDER BY m.ROWID ASC LIMIT 25
    ''',(after,)))


def mapped_owner(sender, direct_verified, allowed):
    if direct_verified != 1:return None
    owner=allowed.get(normalize_sender(sender))
    return owner if owner in {'william','shawn'} else None
