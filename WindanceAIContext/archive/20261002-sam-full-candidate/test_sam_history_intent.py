"""Staged journal integrated with actual SAM helper; no production effects."""
import ast,hashlib,json,sqlite3,tempfile
from pathlib import Path
from typing import Any
import sam_history_intent as journal

path=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
source=path.read_text();node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='post_completed_service_history')
code=ast.get_source_segment(source,node)
old='result = herald_odoo_horse_history(int(horse_id), service_type, date_key, details)'
assert code.count(old)==1
code=code.replace(old,'result = journal.perform(connect, date_key, item["id"], int(horse_id), service_type, details, lambda: herald_odoo_horse_history(int(horse_id), service_type, date_key, details))')
outcomes=[]
for scenario in ['normal','lost_response','malformed_response','local_receipt_failure','changed_payload']:
    with tempfile.TemporaryDirectory(prefix='sam-history-intent-') as directory:
        db=Path(directory)/'fixture.db';sent=[];cleared=[];failed=[False]
        class Connection(sqlite3.Connection):
            def execute(self,sql,*args):
                if scenario=='local_receipt_failure' and sql.lstrip().startswith('INSERT INTO odoo_history_posts') and not failed[0]:
                    failed[0]=True;raise sqlite3.OperationalError('fixture local receipt failure')
                return super().execute(sql,*args)
        def connect():
            c=sqlite3.connect(db,factory=Connection);c.row_factory=sqlite3.Row;return c
        with connect() as c:
            c.executescript('''CREATE TABLE odoo_history_posts(date TEXT,item_id INTEGER,service_type TEXT,odoo_horse_id INTEGER,odoo_history_id INTEGER,created_at TEXT,PRIMARY KEY(date,item_id,service_type));
            CREATE TABLE odoo_service_clear_posts(date TEXT,item_id INTEGER,service_type TEXT,odoo_horse_id INTEGER,odoo_field TEXT,cleared_at TEXT,PRIMARY KEY(date,item_id,service_type));''')
            journal.install(c)
        def remote(*args):
            sent.append(args)
            if scenario in ['lost_response','changed_payload']:raise TimeoutError('synthetic accepted response loss')
            if scenario=='malformed_response':return {'status':'error'}
            return {'status':'ok','record_id':123}
        ns={'Any':Any,'journal':journal,'connect':connect,'now_iso':lambda:'fixture-time','herald_odoo_horse_history':remote,
            'herald_odoo_write':lambda *args:cleared.append(args) or {'status':'ok'}}
        exec(compile(code,'<candidate-history-helper>','exec'),ns)
        item={'id':1,'odoo_horse_id':1,'horse_name':'SYNTHETIC','farrier_text':'synthetic service','farrier_done':1}
        first=ns['post_completed_service_history']('2099-01-01',[item])
        if scenario=='changed_payload':item['farrier_text']='different synthetic service'
        second=ns['post_completed_service_history']('2099-01-01',[item])
        assert len(sent)==1
        held=scenario in ['lost_response','malformed_response','changed_payload']
        assert bool(second['errors'])==held and len(cleared)==(0 if held else 1)
        with connect() as c:state=c.execute('SELECT state FROM sam_history_intents').fetchone()[0]
        assert state==('unconfirmed' if held else 'confirmed')
        outcomes.append({'scenario':scenario,'simulated_creates':len(sent),'held':held,'state':state})
print(json.dumps({'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'candidate_function_sha256':hashlib.sha256(code.encode()).hexdigest(),
                  'cases':outcomes,'production_changes':False,'actual_odoo_calls':0,'model_calls':0,
                  'limits':'No process-exit/concurrency/reconciliation acceptance yet; no existing-intent backfill or deployment'}))
