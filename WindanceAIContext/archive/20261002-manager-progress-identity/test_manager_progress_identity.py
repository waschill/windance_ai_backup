import asyncio,hashlib,importlib.util,json,os,sys,tempfile,time
from pathlib import Path
import receipt_report_transport
from manager_receipt_delivery import RECEIPT
source=Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest()=='15cf1c789e1c1fcef837ed8ccc9e7df9525e73693d7ca9c15be1f279fb38d316'
with tempfile.TemporaryDirectory() as tmp:
    os.environ['VEGA_MANAGER_DATA']=tmp
    spec=importlib.util.spec_from_file_location('fixture_manager',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.init()
    p={'id':'fixture','title':'Synthetic project','owner':'William','stages':[{'key':'stage','task_id':'synthetic-task','status':'running'}]}
    with m.connect() as c:c.execute("INSERT INTO projects(id,status,next_check) VALUES('fixture','active',?)",(time.time()+1000,))
    m.project_view=lambda c,pid:dict(p)
    failure='failed';confirmed=False;calls=[]
    async def http(path,*a,**kw):
        assert path=='/staff/tasks/synthetic-task'
        return {'status':failure}
    m.http=http
    def transport(recipient,body,key,**kw):
        calls.append((body,key,kw['mode']))
        return RECEIPT if confirmed else {'ok':False}
    receipt_report_transport.send_report=transport
    async def attempt():
        try:await m.status_alerts()
        except RuntimeError:
            assert not confirmed
        else:assert confirmed
    asyncio.run(attempt())
    with m.connect() as c:
        pending=json.loads(c.execute("SELECT value FROM state WHERE key='progress:fixture'").fetchone()[0])
        assert 'pending_key' in pending
    failure='blocked';p['title']='Changed title'
    asyncio.run(attempt())
    confirmed=True;asyncio.run(attempt())
    assert len(calls)==3 and len({(body,key) for body,key,mode in calls})==1
    assert [mode for body,key,mode in calls]==['submit','query','query']
    with m.connect() as c:
        done=json.loads(c.execute("SELECT value FROM state WHERE key='progress:fixture'").fetchone()[0])
        assert 'pending_key' not in done
        assert done['failure']==pending['pending_failure']
    # Changed failure becomes a distinct next alert only after prior confirmation.
    asyncio.run(m.status_alerts())
    assert len(calls)==4 and calls[-1][1]!=calls[0][1] and calls[-1][2]=='submit'
    assert len(list(m.app().router.routes()))>0
print(json.dumps({'status':'passed','full_module_import_and_database_init':True,'changed_failure_retains_pending_key':True,'original_body_retained':True,'next_alert_after_confirmation':True,'real_sends':0}))
