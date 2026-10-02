import contextlib,importlib.util,io,json,sqlite3,sys,tempfile
from pathlib import Path
from daily_report_journal import provision
import receipt_report_transport
source=Path(sys.argv[1]);results=[]
receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
with tempfile.TemporaryDirectory(prefix='windance-capture-main-') as tmp:
    for case in ('active','empty','uncertain_then_empty','missing_history','dry_run'):
        spec=importlib.util.spec_from_file_location('capture_durable',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        root=Path(tmp)/case;root.mkdir();m.DELIVERY_JOURNAL=root/'reports.db';m.DB=root/'capture.db'
        with sqlite3.connect(m.DB) as c:
            c.execute('CREATE TABLE captures(state TEXT)')
            if case!='empty':c.executemany('INSERT INTO captures VALUES(?)',[('active',),('active',),('archived',)])
            c.commit()
        if case not in ('missing_history','dry_run'):provision(m.DELIVERY_JOURNAL)
        day=['2026-10-02'];m.report_day=lambda:day[0];calls=[];confirmed=[case!='uncertain_then_empty']
        def send(recipient,body,key,**kwargs):calls.append((body,key,kwargs['mode']));return receipt if confirmed[0] else {'ok':False}
        receipt_report_transport.send_report=send
        def invoke():
            original=sys.argv;sys.argv=['capture']+(['--dry-run'] if case=='dry_run' else [])
            try:
                with contextlib.redirect_stdout(io.StringIO()):return m.main()
            finally:sys.argv=original
        code=invoke()
        if case=='uncertain_then_empty':
            assert code==1 and len(calls)==1
            with sqlite3.connect(m.DB) as c:c.execute('DELETE FROM captures');c.commit()
            day[0]='2026-10-03';confirmed[0]=True
            assert invoke()==0 and len(calls)==2 and calls[0][:2]==calls[1][:2] and calls[1][2]=='query'
            assert invoke()==0 and len(calls)==2
        elif case=='active':assert code==0 and invoke()==0 and len(calls)==1 and '2 active items' in calls[0][0]
        elif case=='missing_history':assert code==1 and not calls and not m.DELIVERY_JOURNAL.exists()
        else:assert code==0 and not calls
        results.append({'case':case,'first_exit':code,'transport_calls':len(calls)})
print(json.dumps({'status':'passed','cases':results,'real_sends':0}))

