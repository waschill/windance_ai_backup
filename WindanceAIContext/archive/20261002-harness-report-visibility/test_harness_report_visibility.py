import ast,contextlib,json,sqlite3,sys,tempfile,__future__
from pathlib import Path
from task_report_journal import provision
a=ast.parse(Path(sys.argv[1]).read_text(encoding='utf-8'))
b=ast.parse(Path(sys.argv[2]).read_text(encoding='utf-8'))
functions=lambda t:{n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
old,new=functions(a),functions(b)
assert set(old)==set(new)
changed={n for n in old if ast.dump(old[n])!=ast.dump(new[n])}
assert changed=={'task_handoff','render_task_handoff'}
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);journal=root/'reports.db';database=root/'harness.db';provision(journal)
    @contextlib.contextmanager
    def db():
        c=sqlite3.connect(database);c.row_factory=sqlite3.Row
        try:
            with c:yield c
        finally:c.close()
    with db() as c:
        c.execute('CREATE TABLE staff_task_notes(id INTEGER,note TEXT,author TEXT,channel TEXT,created_at TEXT,task_id TEXT)')
        c.execute('CREATE TABLE staff_task_deliveries(task_id TEXT,status TEXT)')
        c.execute("INSERT INTO staff_task_deliveries VALUES('legacy','delivered')")
    with sqlite3.connect(journal) as c:c.execute("INSERT INTO reports VALUES('pending:william','PRIVATE_RECIPIENT','PRIVATE_BODY','attempting')")
    ns={'db':db,'TASK_REPORT_JOURNAL':journal}
    module=ast.Module(body=[new[n] for n in ('task_handoff','render_task_handoff')],type_ignores=[])
    exec(compile(module,'actual-visibility','exec',flags=__future__.annotations.compiler_flag),ns)
    for taskid,state,label in [('legacy','legacy_recorded','receipt not independently verified'),('pending','unconfirmed','Unconfirmed'),('absent','not_recorded','No delivery record')]:
        task={'id':taskid,'title':'synthetic','assignee':'fixture','status':'completed','updated_at':'fixed','request':'synthetic','result':'synthetic result'}
        result=ns['task_handoff'](task)
        assert result['william_report_delivery']['state']==state
        rendered=ns['render_task_handoff'](result)
        assert label in rendered and 'PRIVATE_' not in rendered
        assert all(result[k]==v for k,v in task.items())
print(json.dumps({'status':'passed','actual_handoff_and_render_tested':True,'only_two_visibility_functions_changed':True,'private_snapshot_not_exposed':True,'real_sends':0}))
