"""Read-only exact direct-iMessage correlation; no sender or retry capability."""
import sqlite3
from contextlib import closing
from pathlib import Path

def observe(database,recipient,text,after_rowid):
    if type(after_rowid) is not int or after_rowid<0 or not isinstance(recipient,str) or not recipient or not isinstance(text,str) or not text or len(text)>20000:
        return {'status':'unavailable','reason':'invalid_correlation_input'}
    try:
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as c:
            c.execute('PRAGMA query_only=ON')
            budget=[0]
            def bounded():
                budget[0]+=1
                return int(budget[0]>100)
            c.set_progress_handler(bounded,1000)
            rows=c.execute('''SELECT m.ROWID,m.is_sent,m.is_delivered,m.date_delivered,m.error
                FROM message m
                WHERE m.ROWID>? AND m.text=? AND m.service='iMessage' AND m.is_from_me=1
                AND (SELECT COUNT(*) FROM chat_message_join cm WHERE cm.message_id=m.ROWID)=1
                AND EXISTS (
                    SELECT 1 FROM chat_message_join cm
                    JOIN chat_handle_join ch ON ch.chat_id=cm.chat_id
                    JOIN handle h ON h.ROWID=ch.handle_id
                    WHERE cm.message_id=m.ROWID AND h.id=?
                    AND (SELECT COUNT(*) FROM chat_handle_join members WHERE members.chat_id=cm.chat_id)=1
                ) ORDER BY m.ROWID LIMIT 2''',(after_rowid,text,recipient)).fetchall()
        if not rows:return {'status':'unconfirmed','reason':'no_exact_direct_message'}
        if len(rows)!=1:return {'status':'ambiguous','reason':'multiple_exact_messages'}
        rowid,sent,delivered,date_delivered,error=rows[0]
        if error not in (0,None):return {'status':'unconfirmed','reason':'message_error_recorded'}
        if error==0 and sent==1 and delivered==1 and isinstance(date_delivered,(int,float)) and date_delivered>0:
            return {'status':'delivered','evidence':'local_messages_flags','message_rowid':rowid}
        return {'status':'unconfirmed','reason':'delivery_flags_incomplete'}
    except (sqlite3.Error,OSError,ValueError):
        return {'status':'unavailable','reason':'receipt_store_unavailable'}
