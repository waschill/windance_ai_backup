"""Actual candidate delivery function; real disposable journals, fake transport."""
import ast,contextlib,json,re,sqlite3,sys,tempfile,__future__
from pathlib import Path
import receipt_report_transport
from task_report_journal import provision
original=ast.parse(Path(sys.argv[1]).read_text(encoding='utf-8'))
candidate=ast.parse(Path(sys.argv[2]).read_text(encoding='utf-8'))
def functions(tree):return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a,b=functions(original),functions(candidate)
for name,node in a.items():
    if name=='_deliver_staff_task_message':
        old=b['_deliver_staff_task_message_legacy'];saved=old.name;old.name=name
        assert ast.dump(node)==ast.dump(old);old.name=saved
    else:assert ast.dump(node)==ast.dump(b[name]),name
receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
results=[]
with tempfile.TemporaryDirectory() as tmp:
    for case in ('uncertain_changed','legacy_failed','legacy_delivered','missing_history','verified_repeat','ledger_failure','shawn_route'):
        root=Path(tmp)/case;root.mkdir();database=root/'harness.db';journal=root/'reports.db'
        @contextlib.contextmanager
        def db():
            c=sqlite3.connect(database);c.row_factory=sqlite3.Row
            try:
                with c:yield c
            finally:c.close()
        with db() as c:
            c.execute('CREATE TABLE staff_task_deliveries(task_id TEXT PRIMARY KEY,transport TEXT,status TEXT,attempted_at TEXT,delivered_at TEXT,detail TEXT)')
            if case.startswith('legacy_'):c.execute('INSERT INTO staff_task_deliveries(task_id,status) VALUES(?,?)',('task',case[7:]))
        if case!='missing_history':provision(journal)
        calls=[];events=[];shawn=[];confirmed=[case in ('verified_repeat','ledger_failure')]
        def send(to,body,key,**kw):
            calls.append((body,key,kw['mode']));return receipt if confirmed[0] else {'ok':False}
        receipt_report_transport.send_report=send
        ns={'db':db,'TASK_REPORT_JOURNAL':journal,'re':re,'now':lambda:'synthetic-time',
            'audit':lambda *x:events.append(x),'_deliver_staff_task_message_legacy':lambda *x:shawn.append(True)}
        module=ast.Module(body=[b['_deliver_staff_task_message']],type_ignores=[])
        exec(compile(module,'actual-candidate','exec',flags=__future__.annotations.compiler_flag),ns)
        task={'id':'task','assignee':'fixture','title':'synthetic','status':'completed','result':'original report'}
        def invoke():ns['_deliver_staff_task_message'](task,'shawn' if case=='shawn_route' else 'william','/Users/herald/bin/windance_report_send.py')
        if case=='ledger_failure':
            def fail_stamp():raise RuntimeError('synthetic ledger failure')
            ns['now']=fail_stamp
            try:invoke()
            except RuntimeError:pass
            else:raise AssertionError('ledger failure not reached')
            assert len(calls)==1 and not events
            ns['now']=lambda:'synthetic-time'
        invoke()
        if case=='uncertain_changed':
            assert len(calls)==1 and calls[0][2]=='submit'
            with db() as c:assert c.execute('SELECT COUNT(*) FROM staff_task_deliveries').fetchone()[0]==0
            task['result']='changed report';confirmed[0]=True;invoke()
            assert len(calls)==2 and calls[0][:2]==calls[1][:2] and calls[1][2]=='query'
            invoke();assert len(calls)==2 and len(events)==1
        elif case=='verified_repeat':invoke();assert len(calls)==1 and len(events)==1
        elif case=='ledger_failure':assert len(calls)==1 and len(events)==1
        elif case=='shawn_route':assert shawn==[True] and not calls
        else:assert not calls and not events
        with db() as c:
            row=c.execute('SELECT status FROM staff_task_deliveries WHERE task_id=?',('task',)).fetchone()
            if case in ('uncertain_changed','verified_repeat','ledger_failure'):assert row['status']=='delivered'
            elif case.startswith('legacy_'):assert row['status']==case[7:]
        results.append(case)
print(json.dumps({'status':'passed','cases':results,'unrelated_functions_unchanged':True,'real_sends':0,'live_state_changed':False}))
