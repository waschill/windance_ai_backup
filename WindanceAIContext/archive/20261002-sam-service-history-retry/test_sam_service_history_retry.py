"""Actual SAM helper with disposable receipt ledger and synthetic remote service."""
import ast,hashlib,json,sqlite3,tempfile
from pathlib import Path
from typing import Any

path=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
source=path.read_text();node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='post_completed_service_history')
code=ast.get_source_segment(source,node);outcomes=[]
for scenario in ['normal_retry','history_response_lost','clear_response_lost']:
    with tempfile.TemporaryDirectory(prefix='sam-history-retry-') as directory:
        database=Path(directory)/'fixture.db';remote=[];clear_calls=[];lost=[False]
        def connect():
            c=sqlite3.connect(database);c.row_factory=sqlite3.Row;return c
        with connect() as c:
            c.executescript('''CREATE TABLE odoo_history_posts(date TEXT,item_id INTEGER,service_type TEXT,odoo_horse_id INTEGER,odoo_history_id INTEGER,created_at TEXT,PRIMARY KEY(date,item_id,service_type));
            CREATE TABLE odoo_service_clear_posts(date TEXT,item_id INTEGER,service_type TEXT,odoo_horse_id INTEGER,odoo_field TEXT,cleared_at TEXT,PRIMARY KEY(date,item_id,service_type));''')
        def history(*args):
            remote.append(args)
            if scenario=='history_response_lost' and not lost[0]:lost[0]=True;raise TimeoutError('fixture response lost after acceptance')
            return {'status':'ok','record_id':len(remote)}
        def clear(model,record_id,values):
            assert model=='x_horses' and values=={'x_studio_needs_farrier':False}
            clear_calls.append(values)
            if scenario=='clear_response_lost' and not lost[0]:lost[0]=True;raise TimeoutError('fixture clear response lost')
            return {'status':'ok'}
        ns={'Any':Any,'connect':connect,'now_iso':lambda:'fixture-time','herald_odoo_horse_history':history,'herald_odoo_write':clear}
        exec(compile(code,'<actual-service-history>','exec'),ns)
        item={'id':1,'odoo_horse_id':1,'horse_name':'SYNTHETIC','farrier_text':'synthetic completed service','farrier_done':1}
        first=ns['post_completed_service_history']('2099-01-01',[item])
        second=ns['post_completed_service_history']('2099-01-01',[item])
        expected_history=2 if scenario=='history_response_lost' else 1
        expected_clear=2 if scenario=='clear_response_lost' else 1
        assert len(remote)==expected_history and len(clear_calls)==expected_clear
        assert not second['errors']
        outcomes.append({'scenario':scenario,'simulated_history_creates':len(remote),'simulated_need_clears':len(clear_calls),
                         'first_reported_error':bool(first['errors']),'second_reported_error':bool(second['errors'])})
print(json.dumps({'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':outcomes,
 'production_changes':False,'actual_odoo_calls':0,'live_history_read':False,'model_calls':0,
 'limits':'Simulated accepted/lost remote responses; no claim of historical duplicate records or concurrency coverage'}))
