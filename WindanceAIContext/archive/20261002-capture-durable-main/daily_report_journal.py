"""Private daily report snapshots. Runtime never provisions missing history."""
from contextlib import closing
import datetime,fcntl,os,re,sqlite3
from pathlib import Path

def provision(path):
    path=Path(path)
    descriptor=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(descriptor)
    with closing(sqlite3.connect(str(path))) as c:
        c.execute('PRAGMA synchronous=FULL');c.execute('PRAGMA fullfsync=ON')
        c.execute('CREATE TABLE reports(namespace TEXT,day TEXT,recipient TEXT,body TEXT,report_available INTEGER CHECK(report_available IN (0,1)),state TEXT CHECK(state IN (\'ready\',\'attempting\',\'verified\')),PRIMARY KEY(namespace,day))')
        c.execute('PRAGMA user_version=2');c.commit()

def verified(result):
    return (type(result) is dict and result.get('ok') is True and result.get('transport')=='imessage' and
            type(result.get('chunks')) is int and result['chunks']==1 and
            result.get('receipt')=={'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1})

def run_daily(path,namespace,day,recipient,render,transport):
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',namespace):raise ValueError('invalid_namespace')
    if datetime.date.fromisoformat(day).isoformat()!=day:raise ValueError('invalid_day')
    if type(recipient) is not str or not recipient or recipient!=recipient.strip() or len(recipient)>320:raise ValueError('invalid_recipient')
    path=Path(path)
    if not path.is_file():return {'status':'held','reason':'history_missing'}
    with path.with_suffix('.owner.lock').open('a') as owner:
        try:fcntl.flock(owner.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'held','reason':'owner_busy'}
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=rw',uri=True,timeout=2)) as c:
            c.execute('PRAGMA synchronous=FULL');c.execute('PRAGMA fullfsync=ON')
            if c.execute('PRAGMA user_version').fetchone()[0]!=2:return {'status':'held','reason':'history_version'}
            row=c.execute("SELECT day,recipient,body,report_available,state FROM reports WHERE namespace=? AND state!='verified' ORDER BY day LIMIT 1",(namespace,)).fetchone()
            if row is None:row=c.execute('SELECT day,recipient,body,report_available,state FROM reports WHERE namespace=? AND day=?',(namespace,day)).fetchone()
            if row is None:
                rendered=render()
                if rendered is None:return {'status':'not_needed','day':day}
                message,available=rendered if type(rendered) is tuple and len(rendered)==2 else (rendered,True)
                if type(available) is not bool:raise ValueError("invalid_report_availability")
                if type(message) is not str or not message.strip() or len(message)>20000:raise ValueError('invalid_report')
                message=message.strip()
                c.execute('INSERT INTO reports VALUES(?,?,?,?,?,?)',(namespace,day,recipient,message,int(available),'ready'));c.commit()
                row=(day,recipient,message,int(available),'ready')
            saved_day,saved_recipient,body,available,state=row
            if saved_recipient!=recipient:return {'status':'held','reason':'recipient_changed'}
            if state=='verified':return {'status':'verified','day':saved_day,'report_available':bool(available)}
            # A never-attempted older snapshot is not silently submitted tomorrow.
            if saved_day!=day and state=='ready':return {'status':'held','reason':'previous_unattempted_report'}
            mode='query' if state=='attempting' else 'submit'
            if mode=='submit':
                c.execute("UPDATE reports SET state='attempting' WHERE namespace=? AND day=?",(namespace,saved_day));c.commit()
            try:result=transport(saved_recipient,body,namespace+':'+saved_day,mode=mode)
            except Exception:return {'status':'held','reason':'delivery_unknown','day':saved_day}
            if not verified(result):return {'status':'held','reason':'delivery_unconfirmed','day':saved_day}
            c.execute("UPDATE reports SET state='verified' WHERE namespace=? AND day=?",(namespace,saved_day));c.commit()
            return {'status':'verified' if saved_day==day else 'previous_verified','day':saved_day,'report_available':bool(available)}
