"""Exercise actual candidate send/advance with synthetic transport and ledger."""
import ast,asyncio,contextlib,hashlib,json,sqlite3,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
import receipt_report_transport
from manager_receipt_delivery import RECEIPT
source=Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest() in {'4fe10fdbe61a311b04d6cd85c248733ac273e3fae50934c8c519f8828c498ac6','15cf1c789e1c1fcef837ed8ccc9e7df9525e73693d7ca9c15be1f279fb38d316'}
nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name in ('send','send_legacy','advance')]
assert len(nodes)==3
@contextlib.contextmanager
def connect():
    c=sqlite3.connect(database)
    try:
        with c:yield c
    finally:c.close()
with tempfile.TemporaryDirectory() as tmp:
    database=Path(tmp)/'manager.db'
    with connect() as c:
        c.execute('CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT)')
        c.execute('CREATE TABLE projects(id TEXT,status TEXT,report_hash TEXT,delivery TEXT,updated REAL)')
        c.execute('INSERT INTO projects VALUES(?,?,?,?,?)',('fixture','delivery','hash',None,0))
    p={'id':'fixture','status':'delivery','report_hash':'hash','report':'original fixture report','owner':'William','deadline':time.time()+1000}
    calls=[];events=[];confirmed=False;legacy=[]
    def transport(recipient,body,key,**kw):
        calls.append((body,key,kw['mode']))
        return RECEIPT if confirmed else {'ok':False,'status':'legacy_submission'}
    receipt_report_transport.send_report=transport
    def legacy_call(command,**kw):
        assert command[-1]=='/Users/herald/bin/windance_shawn_report_send.py'
        legacy.append(kw['env']['WINDANCE_DELIVERY_KEY'])
        return SimpleNamespace(returncode=0,stdout='ok')
    async def forbidden(*a,**kw):raise AssertionError('task dispatch forbidden')
    scope={'connect':connect,'project_view':lambda c,pid:dict(p),'valid_owner':lambda o:None,
           'asyncio':asyncio,'subprocess':SimpleNamespace(run=legacy_call),'os':__import__('os'),
           'json':json,'time':time,'dumps':json.dumps,'event':lambda *a:events.append(a[2]),'http':forbidden}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
    try:asyncio.run(scope['advance']())
    except RuntimeError:pass
    else:raise AssertionError('legacy evidence accepted')
    with connect() as c:assert c.execute('SELECT status,delivery FROM projects').fetchone()==('delivery',None)
    p['report']='changed fixture report';confirmed=True
    asyncio.run(scope['advance']())
    with connect() as c:assert c.execute('SELECT status FROM projects').fetchone()[0]=='delivered'
    assert calls==[('original fixture report','vega-manager:fixture:report:hash','submit'),('original fixture report','vega-manager:fixture:report:hash','query')]
    assert events==['delivered']
    assert asyncio.run(scope['send']('changed again','fixture:report:hash'))==RECEIPT
    assert len(calls)==2
    assert asyncio.run(scope['send']('fixture','shawn-key','Shawn'))['owner']=='Shawn'
    assert legacy==['vega-manager:shawn-key']
print(json.dumps({'status':'passed','actual_project_completion_guard':True,'original_snapshot_query':True,'verified_no_replay':True,'shawn_legacy_preserved':True,'real_sends':0,'dispatches':0}))
