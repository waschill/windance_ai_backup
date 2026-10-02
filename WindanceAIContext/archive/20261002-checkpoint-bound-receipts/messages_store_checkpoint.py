"""Read-only store checkpoint; no body, recipient or raw GUID leaves the function.

Call within a bounded worker. A checkpoint is not a receipt or a send permission.
"""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3


def hash_values(values):
    return hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()


def checkpoint(database,at_row=None):
    if at_row is not None and (type(at_row) is not int or not 0<at_row<2**63):
        return {'status':'unavailable','reason':'invalid_anchor'}
    try:
        path=Path(database).resolve(strict=True)
        before=path.stat()
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)) as c:
            c.execute('PRAGMA query_only=ON')
            count=[0]
            def progress():
                count[0]+=1
                return int(count[0]>100)
            c.set_progress_handler(progress,1000)
            c.execute('BEGIN')
            return checkpoint_connection(c,path,before,at_row)
    except (OSError,sqlite3.Error,ValueError):
        return {'status':'unavailable','reason':'store_checkpoint_unavailable'}


def checkpoint_connection(c,path,before,at_row):
    first=c.execute('SELECT ROWID,guid FROM message ORDER BY ROWID LIMIT 1').fetchone()
    last=c.execute('SELECT ROWID,guid FROM message ORDER BY ROWID DESC LIMIT 1').fetchone()
    if not first or not last:
        return {'status':'unavailable','reason':'empty_store'}
    boundary=last[0] if at_row is None else at_row
    anchor=last if at_row is None else c.execute('SELECT ROWID,guid FROM message WHERE ROWID=?',(at_row,)).fetchone()
    if not anchor:
        return {'status':'unavailable','reason':'anchor_missing'}
    if any(type(row[1]) is not str or not 1<=len(row[1])<=512 for row in (first,last,anchor)):
        return {'status':'unavailable','reason':'invalid_store_guid'}
    after=path.stat()
    if (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino):
        return {'status':'unavailable','reason':'store_replaced_during_read'}
    return {'status':'captured','store_id':hash_values([before.st_dev,before.st_ino,*first]),
            'high_water':last[0],'boundary':boundary,'anchor':hash_values(list(anchor))}


def same_checkpoint(expected,current):
    return (type(expected) is dict and type(current) is dict and
            expected.get('status')==current.get('status')=='captured' and
            expected.get('store_id')==current.get('store_id') and
            expected.get('boundary')==current.get('boundary') and
            expected.get('anchor')==current.get('anchor') and
            type(current.get('high_water')) is int and
            current['high_water']>=expected['high_water'])
