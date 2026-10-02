"""Full candidate callers and aiohttp lifecycle with disposable state only."""
import asyncio,hashlib,importlib.util,json,os,sys,tempfile,time
from pathlib import Path
from aiohttp.test_utils import TestClient,TestServer
import receipt_report_transport
from manager_receipt_delivery import RECEIPT
source=Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest()=='15cf1c789e1c1fcef837ed8ccc9e7df9525e73693d7ca9c15be1f279fb38d316'
with tempfile.TemporaryDirectory() as tmp:
    os.environ['VEGA_MANAGER_DATA']=tmp
    spec=importlib.util.spec_from_file_location('fixture_manager',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.init()
    async def forbidden(*a,**kw):raise AssertionError('upstream/model/task dispatch forbidden')
    def forbidden_process(*a,**kw):raise AssertionError('external process forbidden')
    m.http=forbidden;m.subprocess.run=forbidden_process
    calls=[];confirmed=False
    def transport(recipient,body,key,**kw):
        calls.append((body,key,kw['mode']))
        return RECEIPT if confirmed else {'ok':False,'status':'uncertain'}
    receipt_report_transport.send_report=transport
    async def exercise():
        global confirmed
        with m.connect() as c:
            c.execute("INSERT INTO messages(id,request,channel,session,status,answer,created,updated,notify,receipt,owner) VALUES(?,?,?,?,?,?,?,?,?,?,?)",('fixture-message','fixture request','fixture','fixture','answered','original answer',1,1,1,None,'William'))
        try:await m.process_messages()
        except RuntimeError:pass
        else:raise AssertionError('uncertain message accepted')
        with m.connect() as c:
            assert c.execute('SELECT receipt FROM messages').fetchone()[0] is None
            c.execute("UPDATE messages SET answer='changed answer'")
        confirmed=True;await m.process_messages();await m.process_messages()
        assert calls==[('Vega: original answer','vega-manager:fixture-message','submit'),('Vega: original answer','vega-manager:fixture-message','query')]
        with m.connect() as c:
            assert json.loads(c.execute('SELECT receipt FROM messages').fetchone()[0])==RECEIPT
            c.execute("INSERT INTO projects(id,title,request,status,plan,updated,next_check,deadline,notified,owner) VALUES(?,?,?,?,?,?,?,?,?,?)",('fixture-project','Original title','fixture request','active','[]',1,time.time()+3600,0,None,'William'))
        confirmed=False
        try:await m.advance()
        except RuntimeError:pass
        else:raise AssertionError('uncertain overdue accepted')
        with m.connect() as c:
            assert c.execute('SELECT notified FROM projects').fetchone()[0] is None
            c.execute("UPDATE projects SET title='Changed title'")
        confirmed=True;await m.advance();await m.advance()
        assert len(calls)==4 and calls[2][:2]==calls[3][:2]
        assert calls[2][1]=='vega-manager:fixture-project:overdue'
        assert [calls[2][2],calls[3][2]]==['submit','query']
        with m.connect() as c:
            assert c.execute('SELECT notified FROM projects').fetchone()[0]=='overdue'
            c.execute("UPDATE projects SET status='paused'")
        client=TestClient(TestServer(m.app()))
        await client.start_server()
        try:
            for _ in range(20):
                response=await client.get('/health');health=await response.json()
                assert response.status==200
                if health['status']=='ok':break
                await asyncio.sleep(.05)
            assert health['status']=='ok'
            response=await client.get('/messages/fixture-message')
            assert response.status==200 and json.loads((await response.json())['receipt'])==RECEIPT
            response=await client.get('/projects')
            assert response.status==200 and (await response.json())[0]['status']=='paused'
        finally:await client.close()
        assert len(calls)==4
        with m.connect() as c:
            assert c.execute("SELECT count(*) FROM events WHERE kind='loop_error'").fetchone()[0]==0
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    asyncio.run(exercise())
print(json.dumps({'status':'passed','actual_message_reply':True,'actual_overdue_alert':True,'changed_text_query_original':True,'service_lifecycle_and_http':True,'clean_shutdown':True,'real_sends':0,'dispatches':0}))
