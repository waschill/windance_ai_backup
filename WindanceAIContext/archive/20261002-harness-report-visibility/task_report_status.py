"""Read-only content-free delivery observation; no enqueue or reconciliation."""
from contextlib import closing
import sqlite3
from pathlib import Path

def status(path,identity,legacy_status=None):
    path=Path(path)
    fallback={'state':'legacy_recorded' if legacy_status=='delivered' else 'legacy_unreconciled','independent_receipt':False} if legacy_status is not None else {'state':'history_unavailable','independent_receipt':False}
    if not path.is_file():return fallback
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.05)) as c:
            steps=[0]
            def bound():
                steps[0]+=1;return int(steps[0]>100)
            c.set_progress_handler(bound,1000)
            if c.execute('PRAGMA user_version').fetchone()[0]!=1:return fallback
            row=c.execute('SELECT state FROM reports WHERE identity=?',(identity,)).fetchone()
        if row is None:return fallback if legacy_status is not None else {'state':'not_recorded','independent_receipt':False}
        mapping={'ready':'pending','attempting':'unconfirmed','verified':'verified'}
        if row[0] not in mapping:return fallback
        return {'state':mapping[row[0]],'independent_receipt':row[0]=='verified'}
    except sqlite3.Error:return fallback
