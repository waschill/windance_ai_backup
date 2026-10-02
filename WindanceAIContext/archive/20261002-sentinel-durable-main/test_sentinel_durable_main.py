import contextlib,importlib.util,io,json,sys,tempfile
from pathlib import Path
from daily_report_journal import provision
import receipt_report_transport

source=Path(sys.argv[1]);results=[]
receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
with tempfile.TemporaryDirectory(prefix='windance-sentinel-main-') as tmp:
    for case in ('normal','midnight','blocked','missing_history'):
        spec=importlib.util.spec_from_file_location('sentinel_durable',source)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        root=Path(tmp)/case;root.mkdir();m.DELIVERY_JOURNAL=root/'reports.db'
        if case!='missing_history':provision(m.DELIVERY_JOURNAL)
        day=['2026-10-02'];m.report_day=lambda:day[0];m.log=lambda text:None
        renders=[];calls=[];confirmed=[case!='midnight']
        def render(minutes):
            renders.append(True)
            return 'Sentinel router review BLOCKED: synthetic missing logs' if case=='blocked' else 'synthetic report '+str(len(renders))
        def send(recipient,message,key,**kwargs):
            calls.append((message,key,kwargs['mode']))
            return receipt if confirmed[0] else {'ok':False,'status':'unknown'}
        m.report=render;receipt_report_transport.send_report=send
        def invoke():
            original=sys.argv;sys.argv=['sentinel']
            try:
                with contextlib.redirect_stdout(io.StringIO()):return m.main()
            finally:sys.argv=original
        first=invoke()
        if case=='missing_history':
            assert first==1 and not renders and not calls and not m.DELIVERY_JOURNAL.exists()
        elif case=='midnight':
            assert first==1
            day[0]='2026-10-03';confirmed[0]=True
            assert invoke()==1 and len(renders)==1
            assert calls[0][:2]==calls[1][:2] and [x[2] for x in calls]==['submit','query']
            assert invoke()==0 and len(renders)==2 and len(calls)==3
            assert calls[-1][1]=='sentinel-router:2026-10-03'
        else:
            assert first==(1 if case=='blocked' else 0)
            assert invoke()==first and len(renders)==1 and len(calls)==1
        results.append({'case':case,'renders':len(renders),'transport_calls':len(calls),'first_exit':first})
print(json.dumps({'status':'passed','cases':results,'real_sends':0}))
