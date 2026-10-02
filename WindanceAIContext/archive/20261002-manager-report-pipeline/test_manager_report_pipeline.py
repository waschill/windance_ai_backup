"""Actual manager send/advance plus candidate wrapper/transport; stub SSH only."""
import ast,asyncio,contextlib,hashlib,importlib.util,io,json,os,sqlite3,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
import receipt_report_transport
from outbox_wire_protocol import envelope,CODES

manager=Path(sys.argv[1]);wrapper=Path(sys.argv[2])
assert hashlib.sha256(manager.read_bytes()).hexdigest()=='0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='6e52cac9d438c1d41b6dde15e3ae12923f66d6659b0f336b7144d368e8c315f7'
nodes=[n for n in ast.parse(manager.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name in ('send','advance')]
assert len(nodes)==2
spec=importlib.util.spec_from_file_location('staged_wrapper',wrapper);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
wire_status=['unknown'];keys=[]
def ssh(command,**kwargs):
    request=json.loads(kwargs['input']);keys.append(request['key'])
    result={'status':wire_status[0]}
    if wire_status[0]=='verified_delivery':result.update(independent_delivery_verified=True,chunks=1)
    return SimpleNamespace(returncode=CODES[wire_status[0]],stdout=json.dumps(envelope(request['key'],request['payload'],result)))
import subprocess
receipt_report_transport.subprocess=SimpleNamespace(run=ssh,TimeoutExpired=subprocess.TimeoutExpired)
def wrapper_call(command,**kwargs):
    assert command[-1]=='/Users/herald/bin/windance_report_send.py' and kwargs['timeout']==90
    assert kwargs['env']['WINDANCE_DELIVERY_KEY']=='vega-manager:synthetic-project:report:synthetic-hash'
    old_stdin=sys.stdin;old_key=os.environ.get('WINDANCE_DELIVERY_KEY');output=io.StringIO()
    sys.stdin=io.StringIO(kwargs['input']);os.environ['WINDANCE_DELIVERY_KEY']=kwargs['env']['WINDANCE_DELIVERY_KEY']
    try:
        with contextlib.redirect_stdout(output):code=w.main()
    finally:
        sys.stdin=old_stdin
        if old_key is None:os.environ.pop('WINDANCE_DELIVERY_KEY',None)
        else:os.environ['WINDANCE_DELIVERY_KEY']=old_key
    return SimpleNamespace(returncode=code,stdout=output.getvalue())

@contextlib.contextmanager
def connect():
    c=sqlite3.connect(database)
    try:
        with c:yield c
    finally:c.close()

with tempfile.TemporaryDirectory(prefix='windance-manager-pipeline-') as tmp:
    database=Path(tmp)/'manager.db'
    with connect() as c:
        c.execute('CREATE TABLE projects(id TEXT,status TEXT,report_hash TEXT,delivery TEXT,updated REAL)')
        c.execute('INSERT INTO projects VALUES(?,?,?,?,?)',('synthetic-project','delivery','synthetic-hash',None,0));c.commit()
    p={'id':'synthetic-project','status':'delivery','report_hash':'synthetic-hash','report':'synthetic report','owner':'William','deadline':time.time()+1000}
    events=[]
    async def forbid(*args,**kwargs):raise AssertionError('unexpected_dispatch')
    scope={'connect':connect,'project_view':lambda c,pid:dict(p),
           'valid_owner':lambda owner:None,'asyncio':asyncio,'subprocess':SimpleNamespace(run=wrapper_call),
           'os':os,'json':json,'time':time,'dumps':json.dumps,'event':lambda *args:events.append(args[2]),'http':forbid}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(manager),'exec'),scope)
    results=[]
    for status in ('unknown','uncertain','legacy_submission','verified_delivery'):
        wire_status[0]=status
        try:asyncio.run(scope['advance']())
        except RuntimeError:assert status!='verified_delivery'
        with connect() as c:row=c.execute('SELECT status,delivery,report_hash FROM projects').fetchone()
        assert row[2]=='synthetic-hash'
        if status=='verified_delivery':assert row[0]=='delivered' and json.loads(row[1])['receipt']['evidence']=='local_messages_flags'
        else:assert row[:2]==('delivery',None)
        results.append({'wire_status':status,'manager_status':row[0]})
    assert len(set(keys))==1 and len(keys)==4 and events==['delivered']
print(json.dumps({'status':'passed','cases':results,'stable_report_key':True,'no_early_completion':True,'real_sends':0,'task_dispatches':0,'shawn_path_tested':False}))
