"""Actual commit renderer composed with staged client and receiver on private fixtures."""
import ast,hashlib,json,secrets,sqlite3,tempfile
from pathlib import Path
from typing import Any
import sam_memory_client as client
import sam_business_memory as receiver
raw=Path('sam_schedule.memory-contract.private.py').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1'
source=raw.decode();node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='commit_day')
original=ast.get_source_segment(source,node)
anchor='result = json_http("POST", f"{HERALD_BASE}/memory", memory_payload, timeout=45)'
assert original.count(anchor)==1
candidate=original.replace(anchor,'result = client_submit(connect, memory_payload, transport)')
class Closing(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
results=[]
for mode in ('normal','lost_first_response','wrong_date','wrong_hash','wrong_event','superseded'):
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);token=secrets.token_urlsafe(32);calls=[]
        def connect():
            c=sqlite3.connect(root/'client.db',factory=Closing);c.row_factory=sqlite3.Row;return c
        def remote():return sqlite3.connect(root/'receiver.db',factory=Closing)
        with connect() as c:
            c.executescript(client.SCHEMA)
            c.execute('CREATE TABLE schedule_days(date TEXT PRIMARY KEY,committed INTEGER,last_committed TEXT,commit_result TEXT)')
            c.execute("INSERT INTO schedule_days(date,committed) VALUES('2026-10-01',0)")
        with remote() as c:c.executescript(receiver.SCHEMA)
        def schedule(date):
            with connect() as c:day=dict(c.execute('SELECT * FROM schedule_days').fetchone())
            return {'date':'2026-10-01','day_name':'Thursday','day':day,'items':[]}
        def transport(envelope):
            calls.append(envelope['event_id'])
            receipt=receiver.record(remote,'Bearer '+token,token,envelope['payload'],
                event_id=envelope['event_id'],expected_revision=envelope['expected_revision'],validate_content=lambda _:True)
            if mode=='lost_first_response' and len(calls)==1:raise OSError('Synthetic lost acknowledgment')
            if mode=='wrong_date':receipt['date']='2026-10-02'
            if mode=='wrong_hash':receipt['content_sha256']='0'*64
            if mode=='wrong_event':receipt['event_id']='wrong-event'
            if mode=='superseded':receipt['superseded']=True
            return receipt
        ns=dict(Any=Any,get_schedule=schedule,connect=connect,json=json,client_submit=client.submit,transport=transport,
                now_iso=lambda:'fixture',log_event=lambda *a,**k:None,
                rollover_unfinished_training=lambda *a:{'enabled':False},post_completed_service_history=lambda *a:{'errors':[],'posted':[]})
        exec(compile(candidate,'<staged-commit-call-seam>','exec'),ns)
        for attempt in range(2):
            try:ns['commit_day']('2026-10-01')
            except (OSError,client.MemoryHeld):pass
            if mode=='lost_first_response' and attempt==0:
                with connect() as c:assert c.execute('SELECT committed FROM schedule_days').fetchone()[0]==0
        with connect() as c:
            committed=c.execute('SELECT committed FROM schedule_days').fetchone()[0]
            state=c.execute('SELECT state FROM sam_memory_requests').fetchone()[0]
        with remote() as c:assert c.execute('SELECT count(*) FROM sam_business_receipts').fetchone()[0]==1
        assert len(set(calls))==1
        assert bool(committed)==(mode in ('normal','lost_first_response'))
        assert state==('confirmed' if committed else 'pending')
        results.append({'case':mode,'committed':bool(committed),'client_state':state,'receiver_commits':1,'stable_retry_identity':True})
print(json.dumps({'cases':results,'actual_api_calls':0,'actual_odoo_calls':0,'production_changes':False}))
