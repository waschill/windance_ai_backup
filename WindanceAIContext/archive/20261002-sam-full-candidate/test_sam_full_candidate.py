"""Actual candidate schema plus composed commit/history/HTTP functions; isolated."""
import ast,hashlib,io,json,sqlite3,tempfile,urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any
path=Path('/home/williamschilling/backups/sam-reliability-candidate-20261002/sam_schedule.candidate.private.py')
source=path.read_text();names={'connect','init_db','commit_day','post_completed_service_history','json_http'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==len(names)
outcomes=[]
for mode in ['normal','late_memory_error','history_response_lost']:
    with tempfile.TemporaryDirectory(prefix='sam-full-candidate-') as directory:
        root=Path(directory);creates=[];clears=[];posts=[]
        item={'id':'fixture-item-uuid','odoo_horse_id':1,'horse_name':'SYNTHETIC','farrier_text':'synthetic service','farrier_done':1}
        def history(*args):
            creates.append(args)
            if mode=='history_response_lost':raise TimeoutError('fixture acceptance then response loss')
            return {'status':'ok','record_id':123}
        def http(request,timeout):
            posts.append(json.loads(request.data))
            body={'status':'error'} if mode=='late_memory_error' and len(posts)==1 else {'status':'ok'}
            return io.BytesIO(json.dumps(body).encode())
        ns={'Any':Any,'sqlite3':sqlite3,'DATA_DIR':root,'DB_PATH':root/'fixture.db','DEFAULT_TRAINERS':[],
            'now_iso':lambda:'fixture-time','json':json,'HERALD_BASE':'http://fixture.invalid',
            'urllib':SimpleNamespace(request=SimpleNamespace(Request=urllib.request.Request,urlopen=http)),
            'rollover_unfinished_training':lambda *a:{'enabled':False},'herald_odoo_horse_history':history,
            'herald_odoo_write':lambda *a:clears.append(a) or {'status':'ok'},'log_event':lambda *a,**k:None}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-candidate-functions>','exec'),ns)
        ns['init_db']()
        with ns['connect']() as c:
            c.execute("INSERT INTO schedule_days(date,day_name) VALUES('2099-01-01','fixture-day')");c.commit()
        def schedule(date):
            with ns['connect']() as c:row=dict(c.execute('SELECT * FROM schedule_days').fetchone())
            return {'date':'2099-01-01','day_name':'fixture-day','day':row,'items':[item]}
        ns['get_schedule']=schedule
        errors=[]
        for attempt in range(2):
            try:ns['commit_day']('2099-01-01');errors.append(False)
            except RuntimeError:errors.append(True)
        ns['init_db']() # Repeated real schema initialization must preserve intent.
        with ns['connect']() as c:
            committed=c.execute('SELECT committed FROM schedule_days').fetchone()[0]
            state=c.execute('SELECT state FROM sam_history_intents').fetchone()[0]
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert len(creates)==1
        if mode=='history_response_lost':assert committed==0 and state=='unconfirmed' and not clears and not posts and errors==[True,True]
        else:assert committed==1 and state=='confirmed' and len(clears)==1
        if mode=='late_memory_error':assert errors==[True,False] and len(posts)==2
        outcomes.append({'scenario':mode,'simulated_creates':len(creates),'simulated_clears':len(clears),
                         'memory_posts':len(posts),'committed':bool(committed),'intent_state':state})
print(json.dumps({'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'actual_candidate_schema_and_functions':True,
                  'text_item_ids_supported':True,'cases':outcomes,'production_changes':False,'actual_odoo_calls':0,
                  'limits':'No full module startup, scheduler, HTTP listener or real data; reconciliation/clear concurrency still open'}))
