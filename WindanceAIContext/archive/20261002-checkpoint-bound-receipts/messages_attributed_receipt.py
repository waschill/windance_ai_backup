"""Staged read-only receipt correlation. Must run inside a bounded worker.

No sending, replay, queue mutation or trusted baseline creation is provided here.
"""
import sqlite3
from contextlib import closing
from pathlib import Path
from attributed_text_candidate import decode_text
from messages_store_checkpoint import checkpoint_connection,same_checkpoint


def observe(database, recipient, text, after_rowid, expected_checkpoint=None):
    if (type(after_rowid) is not int or not 0 <= after_rowid < 2**63
            or type(recipient) is not str or not recipient or len(recipient)>320
            or type(text) is not str or not text or len(text)>20000):
        return {'status':'unavailable','reason':'invalid_correlation_input'}
    try:
        path=Path(database).resolve(strict=True)
        before=path.stat()
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as c:
            c.execute('PRAGMA query_only=ON')
            budget = [0]
            def bounded():
                budget[0] += 1
                return int(budget[0]>100)
            c.set_progress_handler(bounded,1000)
            c.execute('BEGIN')
            if expected_checkpoint is not None:
                if expected_checkpoint.get('boundary')!=after_rowid or not same_checkpoint(expected_checkpoint,checkpoint_connection(c,path,before,after_rowid)):
                    return {'status':'unconfirmed','reason':'message_store_changed'}
            rows=c.execute('''SELECT m.ROWID,m.is_sent,m.is_delivered,m.date_delivered,m.error,
                CASE WHEN length(m.text)<=20000 THEN m.text ELSE NULL END,length(m.text),
                CASE WHEN length(m.attributedBody)<=262144 THEN m.attributedBody ELSE NULL END,
                length(m.attributedBody)
                FROM message m WHERE m.ROWID>? AND m.service='iMessage' AND m.is_from_me=1
                AND (SELECT COUNT(*) FROM chat_message_join cm WHERE cm.message_id=m.ROWID)=1
                AND EXISTS (
                    SELECT 1 FROM chat_message_join cm JOIN chat_handle_join ch ON ch.chat_id=cm.chat_id
                    JOIN handle h ON h.ROWID=ch.handle_id
                    WHERE cm.message_id=m.ROWID AND h.id=?
                    AND (SELECT COUNT(*) FROM chat_handle_join members WHERE members.chat_id=cm.chat_id)=1
                ) ORDER BY m.ROWID LIMIT 101''',(after_rowid,recipient))
            matches=[]
            unknown=False
            for count,row in enumerate(rows,1):
                if count>100:
                    return {'status':'unconfirmed','reason':'candidate_limit_exceeded'}
                rowid,sent,delivered,date,error,plain,plain_size,blob,blob_size=row
                if (plain_size or 0)>20000 or (blob_size or 0)>262144:
                    unknown=True
                    continue
                if blob_size:
                    decoded=decode_text(blob)
                    if decoded is None or (plain and plain!=decoded):
                        unknown=True
                        continue
                    actual=decoded
                else:
                    actual=plain
                if type(actual) is not str:
                    unknown=True
                    continue
                if actual==text:
                    matches.append((rowid,sent,delivered,date,error))
            # An unreadable candidate might be another match; never hide ambiguity.
            if unknown:
                return {'status':'unconfirmed','reason':'candidate_content_unverifiable'}
            if expected_checkpoint is not None and not same_checkpoint(expected_checkpoint,checkpoint_connection(c,path,before,after_rowid)):
                return {'status':'unconfirmed','reason':'message_store_changed'}
        if not matches:
            return {'status':'unconfirmed','reason':'no_exact_direct_message'}
        if len(matches)!=1:
            return {'status':'ambiguous','reason':'multiple_exact_messages'}
        rowid,sent,delivered,date,error=matches[0]
        if error not in (0,None):
            return {'status':'unconfirmed','reason':'message_error_recorded'}
        if error==0 and sent==1 and delivered==1 and type(date) in (int,float) and date>0:
            return {'status':'delivered','evidence':'local_messages_flags','message_rowid':rowid}
        return {'status':'unconfirmed','reason':'delivery_flags_incomplete'}
    except (sqlite3.Error,OSError,ValueError,OverflowError):
        return {'status':'unavailable','reason':'receipt_store_unavailable'}
