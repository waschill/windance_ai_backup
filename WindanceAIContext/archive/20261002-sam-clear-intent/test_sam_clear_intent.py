"""Actual helper comparison; all remote effects are synthetic callbacks."""
import ast,hashlib,json,sqlite3,tempfile
from pathlib import Path
from typing import Any
from sam_clear_intent import install,perform
path=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
source=path.read_text();assert hashlib.sha256(path.read_bytes()).hexdigest()=='824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1'
node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='post_completed_service_history')
original=ast.get_source_segment(source,node)
anchor='herald_odoo_write("x_horses", int(horse_id), {needs_field: False})'
assert original.count(anchor)==1
candidate=original.replace(anchor,'clear_once(connect, date_key, item["id"], int(horse_id), service_type, int(history_receipt["odoo_history_id"]) if history_receipt else history_id, lambda: herald_odoo_write("x_horses", int(horse_id), {needs_field: False}))')
results=[]
for version,code in [('baseline',original),('candidate',candidate)]:
 for mode in ['normal','lost_response_new_need','application_error','false_write_result','wrong_record_receipt','receipt_failure_new_need']:
  with tempfile.TemporaryDirectory(prefix='sam-clear-intent-') as directory:
   database=Path(directory)/'fixture.db';calls=[];remote={'needs':True}
   def connect():
    c=sqlite3.connect(database);c.row_factory=sqlite3.Row;return c
   with connect() as c:
    c.executescript('''CREATE TABLE odoo_history_posts(date TEXT,item_id TEXT,service_type TEXT,odoo_horse_id INTEGER,odoo_history_id INTEGER,created_at TEXT,PRIMARY KEY(date,item_id,service_type));
    CREATE TABLE odoo_service_clear_posts(date TEXT,item_id TEXT,service_type TEXT,odoo_horse_id INTEGER,odoo_field TEXT,cleared_at TEXT,PRIMARY KEY(date,item_id,service_type));''')
    install(c)
    if mode=='receipt_failure_new_need':c.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON odoo_service_clear_posts BEGIN SELECT RAISE(ABORT,'fixture receipt failure'); END")
   def clear(model,record,values):
    assert model=='x_horses' and record==1 and values=={'x_studio_needs_farrier':False}
    calls.append(1)
    if mode=='application_error':return {'status':'error'}
    if mode in ['false_write_result','wrong_record_receipt']:return {'status':'ok','model':model,'record_id':2 if mode=='wrong_record_receipt' else record,'fields':list(values),'result':mode!='false_write_result'}
    remote['needs']=False
    if mode=='lost_response_new_need' and len(calls)==1:raise TimeoutError('synthetic accepted response loss')
    return {'status':'ok','model':model,'record_id':record,'fields':list(values),'result':True}
   ns={'Any':Any,'connect':connect,'clear_once':perform,'now_iso':lambda:'fixture-time','herald_odoo_horse_history':lambda *a:{'status':'ok','record_id':123},'herald_odoo_write':clear}
   exec(compile(code,'<actual-helper-candidate>','exec'),ns)
   item={'id':'synthetic-item','odoo_horse_id':1,'horse_name':'SYNTHETIC','farrier_text':'synthetic completed service','farrier_done':1}
   first=ns['post_completed_service_history']('2099-01-01',[item])
   if mode in ['lost_response_new_need','receipt_failure_new_need']:remote['needs']=True
   if mode=='receipt_failure_new_need':
    with connect() as c:c.execute('DROP TRIGGER fail_receipt')
   second=ns['post_completed_service_history']('2099-01-01',[item])
   with connect() as c:receipts=c.execute('SELECT COUNT(*) FROM odoo_service_clear_posts').fetchone()[0]
   if version=='candidate':
    assert len(calls)==1
    if mode in ['lost_response_new_need','application_error','false_write_result','wrong_record_receipt']:assert receipts==0 and second['errors']
    else:assert receipts==1 and not second['errors']
    if mode!='normal':assert remote['needs']
   else:
    if mode in ['lost_response_new_need','receipt_failure_new_need']:assert len(calls)==2 and not remote['needs']
    if mode in ['application_error','false_write_result','wrong_record_receipt']:assert receipts==1 and not first['errors']
   results.append({'version':version,'scenario':mode,'simulated_clears':len(calls),'new_need_preserved':remote['needs'] if 'new_need' in mode else None,'receipts':receipts,'second_error':bool(second['errors'])})
print(json.dumps({'cases':results,'candidate_helper_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'production_changes':False,'actual_odoo_calls':0,'limits':'No Odoo atomic version check; first-attempt stale need, pre-existing receipts, full composition and authoritative reconciliation remain open'}))
