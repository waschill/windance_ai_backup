import contextlib,json,sqlite3,tempfile
from pathlib import Path
from manager_receipt_delivery import deliver,RECEIPT

with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'manager.db'
    @contextlib.contextmanager
    def connect():
        c=sqlite3.connect(path)
        try:
            with c:yield c
        finally:c.close()
    with connect() as c:c.execute('CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT)')
    def corrupt(*args,**kw):
        with connect() as c:
            row=c.execute('SELECT key,value FROM state').fetchone()
            value=json.loads(row[1]);value['body']='different snapshot'
            c.execute('UPDATE state SET value=? WHERE key=?',(json.dumps(value),row[0]))
        return RECEIPT
    try:deliver(connect,'fixture-owner','original','race',corrupt)
    except RuntimeError as e:assert str(e)=='delivery_snapshot_changed'
    else:raise AssertionError('changed snapshot overwritten')
    with connect() as c:
        value=json.loads(c.execute('SELECT value FROM state').fetchone()[0])
        assert value['phase']=='attempting' and value['body']=='different snapshot'
        c.execute('DELETE FROM state')
    def concurrent(*args,**kw):
        with connect() as c:
            row=c.execute('SELECT key,value FROM state').fetchone()
            value=json.loads(row[1]);value['phase']='verified'
            c.execute('UPDATE state SET value=? WHERE key=?',(json.dumps(value,sort_keys=True),row[0]))
        return RECEIPT
    result=deliver(connect,'fixture-owner','original','concurrent',concurrent)
    result['receipt']['ok']=False
    assert RECEIPT['receipt']['ok'] is True
    def forbidden(*a,**kw):raise AssertionError('replay')
    assert deliver(connect,'fixture-owner','changed','concurrent',forbidden)==RECEIPT
print(json.dumps({'status':'passed','snapshot_change_held':True,'same_snapshot_concurrent_confirmation':True,'receipt_copy_isolated':True,'real_sends':0}))
