"""Actual SAM commit renderer against staged admission; all effects synthetic."""
import ast,hashlib,json,secrets,sqlite3,tempfile
from pathlib import Path
from typing import Any
from sam_memory_contract import admit,ProducerDenied
p=Path('sam_schedule.memory-contract.private.py');raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1'
source=raw.decode('utf-8');node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='commit_day')
results=[]
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
for mode in ('empty','mixed','unicode','oversized','lost_first_response'):
    with tempfile.TemporaryDirectory() as folder:
        db=Path(folder)/'fixture.db';token=secrets.token_urlsafe(32);accepted=[];sizes=[]
        def connect():
            c=sqlite3.connect(db,factory=ClosingConnection);c.row_factory=sqlite3.Row;return c
        with connect() as c:
            c.execute('CREATE TABLE schedule_days(date TEXT PRIMARY KEY,committed INTEGER,last_committed TEXT,commit_result TEXT)')
            c.execute("INSERT INTO schedule_days(date,committed) VALUES('2026-10-01',0)")
            c.execute('CREATE TABLE training_completion_details(item_id TEXT,category TEXT,subcategory TEXT,note TEXT,stars INTEGER)')
        item={'id':'synthetic','horse_name':'Synthetic','training_raw':'R','training_done':1,
              'farrier_text':'Synthetic service','farrier_done':0,'vet_text':'Synthetic service','vet_done':1}
        if mode=='unicode':item['horse_name']='Synthetic \u00e9\u9a6c'
        if mode=='oversized':item['vet_text']='x'*65536
        items=[] if mode=='empty' else [item]
        def schedule(date):
            with connect() as c:day=dict(c.execute('SELECT * FROM schedule_days').fetchone())
            return {'date':'2026-10-01','day_name':'Thursday','day':day,'items':items}
        def http(method,url,payload,timeout):
            assert (method,url,timeout)==('POST','http://fixture.invalid/memory',45)
            sizes.append(len(payload['value'].encode()))
            record=admit('Bearer '+token,token,payload,lambda text:True)
            accepted.append(record['content_sha256'])
            if mode=='lost_first_response' and len(accepted)==1:raise OSError('Synthetic lost acknowledgment')
            return {'status':'ok'}
        ns=dict(Any=Any,get_schedule=schedule,connect=connect,json=json,HERALD_BASE='http://fixture.invalid',
                json_http=http,now_iso=lambda:'fixture-time',log_event=lambda *a,**k:None,
                rollover_unfinished_training=lambda *a:{'enabled':False},
                post_completed_service_history=lambda *a:{'errors':[],'posted':[]})
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-SAM-commit-renderer>','exec'),ns)
        failed=False
        try:ns['commit_day']('2026-10-01')
        except (ProducerDenied,OSError):failed=True
        with connect() as c:first_committed=c.execute('SELECT committed FROM schedule_days').fetchone()[0]
        if mode in ('oversized','lost_first_response'):assert failed and first_committed==0
        else:assert not failed and first_committed==1
        if mode=='lost_first_response':
            ns['commit_day']('2026-10-01');assert len(accepted)==2 and accepted[0]==accepted[1]
        if mode!='oversized':
            before=len(accepted);ns['commit_day']('2026-10-01');assert len(accepted)==before
        results.append({'case':mode,'rendered_bytes':sizes[0],'first_local_committed':bool(first_committed),
                        'admitted_attempts':len(accepted),'already_committed_repost':False})
print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'cases':results,
                  'actual_api_calls':0,'actual_odoo_calls':0,'actual_notes_used':False}))
