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
    calls=[]
    def unknown(to,text,key,**kw):calls.append((to,text,key,kw['mode']));return {'ok':False}
    for text in ('original report','changed report'):
        try:deliver(connect,'synthetic-owner',text,'message-key',unknown)
        except RuntimeError:pass
        else:raise AssertionError('false delivery')
    assert calls==[('synthetic-owner','original report','vega-manager:message-key','submit'),('synthetic-owner','original report','vega-manager:message-key','query')]
    def confirmed(to,text,key,**kw):
        assert (to,text,key,kw['mode'])==calls[1];return RECEIPT
    assert deliver(connect,'synthetic-owner','changed again','message-key',confirmed)==RECEIPT
    def forbidden(*a,**kw):raise AssertionError('duplicate transport')
    assert deliver(connect,'synthetic-owner','changed once more','message-key',forbidden)==RECEIPT
    try:deliver(connect,'different-owner','body','message-key',forbidden)
    except ValueError:pass
    else:raise AssertionError('recipient change accepted')
    with connect() as c:assert c.execute('SELECT COUNT(*) FROM state').fetchone()[0]==1
print(json.dumps({'status':'passed','original_wire_key_preserved':True,'changed_body_reconciles_original':True,'verified_no_replay':True,'recipient_change_held':True,'real_sends':0}))
