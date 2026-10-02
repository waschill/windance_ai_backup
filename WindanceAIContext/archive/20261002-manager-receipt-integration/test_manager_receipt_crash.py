import contextlib,json,os,sqlite3,subprocess,sys,tempfile
from pathlib import Path
from manager_receipt_delivery import deliver,RECEIPT
@contextlib.contextmanager
def connect():
    c=sqlite3.connect(database)
    try:
        with c:yield c
    finally:c.close()
if len(sys.argv)>1:
    database=Path(sys.argv[1])
    def terminate(*a,**kw):
        assert kw['mode']=='submit'
        os._exit(23)
    deliver(connect,'synthetic-owner','original before crash','crash-key',terminate)
    raise AssertionError('child survived')
with tempfile.TemporaryDirectory() as tmp:
    database=Path(tmp)/'state.db'
    with connect() as c:c.execute('CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT)')
    child=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(database)],capture_output=True,timeout=15)
    assert child.returncode==23
    with connect() as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        saved=json.loads(c.execute('SELECT value FROM state').fetchone()[0])
        assert saved['phase']=='attempting'
    calls=[]
    def query(recipient,body,key,**kw):
        calls.append(kw['mode'])
        assert body=='original before crash' and key=='vega-manager:crash-key'
        return RECEIPT
    assert deliver(connect,'synthetic-owner','different after crash','crash-key',query)==RECEIPT
    assert calls==['query']
print(json.dumps({'status':'passed','abrupt_process_exit':23,'durable_attempt_snapshot':True,'restart_query_only':True,'real_sends':0}))
