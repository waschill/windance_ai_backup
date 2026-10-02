"""Private immutable task-report snapshots; no automatic legacy adoption."""
from contextlib import closing
import fcntl,hashlib,os,sqlite3
from pathlib import Path
from daily_report_journal import verified

def provision(path):
    path=Path(path)
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    with closing(sqlite3.connect(str(path))) as c:
        c.execute('PRAGMA synchronous=FULL');c.execute('PRAGMA fullfsync=ON')
        c.execute("CREATE TABLE reports(identity TEXT PRIMARY KEY,recipient TEXT NOT NULL,body TEXT NOT NULL,state TEXT CHECK(state IN ('ready','attempting','verified')) NOT NULL)")
        c.execute('PRAGMA user_version=1');c.commit()

def run_task(path,identity,recipient,render,legacy_exists,transport):
    for value,limit in ((identity,512),(recipient,320)):
        if type(value) is not str or not value.strip() or value!=value.strip() or len(value)>limit:
            raise ValueError('invalid_report_identity')
    path=Path(path)
    if not path.is_file():return {'status':'held','reason':'history_missing'}
    with path.with_suffix('.owner.lock').open('a') as owner:
        try:fcntl.flock(owner.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'held','reason':'owner_busy'}
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=rw',uri=True,timeout=2)) as c:
            c.execute('PRAGMA synchronous=FULL');c.execute('PRAGMA fullfsync=ON')
            if c.execute('PRAGMA user_version').fetchone()[0]!=1:return {'status':'held','reason':'history_version'}
            row=c.execute('SELECT recipient,body,state FROM reports WHERE identity=?',(identity,)).fetchone()
            if row is None:
                # Require an explicit negative answer, never infer from None/error.
                if legacy_exists() is not False:return {'status':'held','reason':'legacy_history_unreconciled'}
                body=render()
                if type(body) is not str or not body.strip() or len(body)>20000:raise ValueError('invalid_report')
                body=body.strip()
                c.execute("INSERT INTO reports VALUES(?,?,?,'ready')",(identity,recipient,body));c.commit()
                row=(recipient,body,'ready')
            saved_recipient,body,state=row
            if saved_recipient!=recipient:return {'status':'held','reason':'recipient_changed'}
            if state=='verified':return {'status':'verified'}
            mode='query' if state=='attempting' else 'submit'
            if mode=='submit':
                c.execute("UPDATE reports SET state='attempting' WHERE identity=?",(identity,));c.commit()
            key='harness-task:'+hashlib.sha256(identity.encode()).hexdigest()
            try:result=transport(saved_recipient,body,key,mode=mode)
            except Exception:return {'status':'held','reason':'delivery_unknown'}
            if not verified(result):return {'status':'held','reason':'delivery_unconfirmed'}
            c.execute("UPDATE reports SET state='verified' WHERE identity=?",(identity,));c.commit()
            return {'status':'verified'}
