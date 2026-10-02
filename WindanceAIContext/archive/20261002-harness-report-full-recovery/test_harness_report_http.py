"""Full candidate import/startup and ASGI requests, with outbound/write guards."""
import asyncio,importlib.util,json,os,sys,tempfile
from pathlib import Path
source=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(source.parent))
with tempfile.TemporaryDirectory(prefix='harness-report-http-') as tmp:
    scratch=Path(tmp).resolve()
    for key in ('DATA','CONFIG','LOG'):os.environ['AGENT_HARNESS_'+key+'_DIR']=str(scratch)
    for key in ('GOOGLE_WORKSPACE_CONFIG_DIR','EXCALIDRAW_DIR'):os.environ[key]=str(scratch)
    os.environ['HERMES_MEMORY_FILE']=str(scratch/'unused-memory.md')
    os.environ['AGENT_HARNESS_TOKEN']='synthetic-isolation-token'
    def guard(event,args):
        if event in ('subprocess.Popen','os.system','socket.connect','socket.bind','socket.sendto'):
            raise AssertionError('external operation forbidden')
        if event=='sqlite3.connect':
            path=os.fsdecode(args[0]);assert str(scratch) in path,'non-fixture database'
        if event=='open' and not isinstance(args[0],int):
            path,mode,flags=args
            if (flags or 0)&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
                assert Path(os.fsdecode(path)).resolve().is_relative_to(scratch),'non-fixture write'
    sys.addaudithook(guard)
    spec=importlib.util.spec_from_file_location('harness_candidate_http',source)
    h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
    h.TASK_REPORT_JOURNAL=scratch/'task-report-delivery.db'
    h.startup()
    from task_report_journal import provision
    provision(h.TASK_REPORT_JOURNAL)
    import receipt_report_transport,httpx
    calls=[];confirmed=[False]
    receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
    def transport(to,body,key,**kw):
        calls.append((body,key,kw['mode']));return receipt if confirmed[0] else {'ok':False}
    receipt_report_transport.send_report=transport
    task={'id':'synthetic-report-task','assignee':'Forge','title':'Synthetic report','request':'synthetic request',
          'requester':'william','channel':'imessage','priority':'normal','status':'completed','result':'Original synthetic result',
          'source':'max-imessage-fixture','created_at':'fixed','updated_at':'fixed'}
    with h.db() as c:
        keys=list(task)
        c.execute('INSERT INTO staff_tasks('+','.join(keys)+') VALUES('+','.join('?' for _ in keys)+')',tuple(task.values()));c.commit()
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://fixture') as client:
            assert (await client.get('/staff/tasks')).status_code==401
            headers={'Authorization':'Bearer synthetic-isolation-token'}
            first=await client.get('/staff/tasks',headers=headers)
            assert first.status_code==200 and first.json()['tasks'][0]['william_report_delivery']['state']=='not_recorded'
            h.deliver_staff_task_result(task)
            response=await client.get('/staff/tasks/synthetic-report-task',headers=headers)
            assert response.json()['task']['william_report_delivery']['state']=='unconfirmed'
            task['result']='Changed synthetic result';confirmed[0]=True
            h.deliver_staff_task_result(task);h.deliver_staff_task_result(task)
            response=await client.get('/staff/tasks/synthetic-report-task',headers=headers)
            assert response.json()['task']['william_report_delivery']=={'state':'verified','independent_receipt':True}
            assert len(calls)==2 and calls[0][:2]==calls[1][:2] and [x[2] for x in calls]==['submit','query']
            response=await client.post('/message',headers=headers,json={'message':'remember this: password: SYNTHETIC_PRIVATE_MARKER','user':'William','channel':'vega-internal','request_id':'fixture-memory'})
            assert response.status_code==200 and response.json()['model']=='memory-guard'
            assert 'SYNTHETIC_PRIVATE_MARKER' not in response.text
            with h.db() as c:
                assert c.execute("SELECT COUNT(*) FROM audit_log WHERE payload_json LIKE '%SYNTHETIC_PRIVATE_MARKER%'").fetchone()[0]==0
    asyncio.run(check())
    service_modules=sorted({Path(m.__file__).name for m in sys.modules.values() if getattr(m,'__file__',None) and str(m.__file__).startswith('/Users/herald/services/agent-harness/')})
    print(json.dumps({'status':'passed','complete_candidate_startup':True,'asgi_auth_and_delivery_states':True,'live_service_module_dependencies':service_modules,
                      'original_snapshot_retained':True,'memory_guard_preserved':True,'external_operations_blocked':True,
                      'real_sends':0,'live_writes':0,'schedulers_enabled':False}))
