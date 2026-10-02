"""Actual staged SAM schema and commit functions, isolated SQLite and fake Odoo."""
import ast, hashlib, json, os, secrets, sqlite3, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
import sam_business_memory as receiver

root=Path(__file__).parent/'sam-memory-r3-private'
manifest=json.loads((root/'memory-r3-manifest.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in manifest.items())
sys.path.insert(0,str(root))
import sam_memory_transport
source=(root/'sam_schedule.memory-r3.private.py').read_text(encoding='utf-8')
names={'connect','init_db','commit_day','post_completed_service_history','post_sam_business_memory'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names]
assert len(nodes)==len(names)
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
def local_connect(*args,**kwargs):
    return sqlite3.connect(*args,**kwargs,factory=ClosingConnection)

results=[]
for mode in ('normal','memory_lost','wrong_receipt','missing_config','history_lost','clear_lost_new_need','clear_false','clear_receipt_failure_new_need'):
    with tempfile.TemporaryDirectory(prefix='sam-memory-r3-') as directory:
        folder=Path(directory);creates=[];clears=[];posts=[];remote={'need':True}
        credential=secrets.token_hex(24)
        def receiver_connect():return local_connect(folder/'receiver.db')
        with receiver_connect() as c:c.executescript(receiver.SCHEMA)
        def history(*args):
            creates.append(1)
            if mode=='history_lost':raise TimeoutError('synthetic lost history acknowledgment')
            return {'status':'ok','record_id':123}
        def clear(model,record,values):
            clears.append(1)
            if mode=='clear_false':return {'status':'ok','result':False,'model':model,'record_id':record,'fields':list(values)}
            remote['need']=False
            if mode=='clear_lost_new_need':raise TimeoutError('synthetic lost clear acknowledgment')
            return {'status':'ok','result':True,'model':model,'record_id':record,'fields':list(values)}
        def transport(url,path,envelope):
            posts.append(envelope['event_id'])
            result=receiver.record(receiver_connect,'Bearer '+credential,credential,envelope['payload'],event_id=envelope['event_id'],expected_revision=envelope['expected_revision'],validate_content=lambda _:True)
            if mode=='memory_lost' and len(posts)==1:raise RuntimeError('synthetic lost memory response')
            if mode=='wrong_receipt':result['event_id']='wrong-event'
            return result
        ns={'Any':Any,'sqlite3':SimpleNamespace(connect=local_connect,Row=sqlite3.Row,Connection=sqlite3.Connection),'DATA_DIR':folder,'DB_PATH':folder/'sam.db','DEFAULT_TRAINERS':[],
            'now_iso':lambda:'fixture','json':json,'HERALD_BASE':'http://fixture.invalid',
            'rollover_unfinished_training':lambda *a:{'enabled':False},'herald_odoo_horse_history':history,
            'herald_odoo_write':clear,'log_event':lambda *a,**k:None}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<r3-composed>','exec'),ns)
        ns['init_db']()
        with ns['connect']() as c:
            c.execute("INSERT INTO schedule_days(date,day_name) VALUES('2099-01-01','fixture')")
            if mode=='clear_receipt_failure_new_need':c.execute("CREATE TRIGGER receipt_failure BEFORE INSERT ON odoo_service_clear_posts BEGIN SELECT RAISE(ABORT,'fixture receipt failure'); END")
        def schedule(date):
            with ns['connect']() as c:day=dict(c.execute('SELECT * FROM schedule_days').fetchone())
            return {'date':'2099-01-01','day_name':'fixture','day':day,'items':[{'id':'fixture-text-id','odoo_horse_id':1,'horse_name':'SYNTHETIC','farrier_text':'synthetic service','farrier_done':1}]}
        ns['get_schedule']=schedule;errors=[];error_types=[];error_messages=[]
        env={'SAM_BUSINESS_MEMORY_URL':'https://fixture.invalid/memory/business/sam-schedule','SAM_BUSINESS_MEMORY_CREDENTIAL_FILE':'fixture-only'}
        if mode=='missing_config':env={}
        with patch.dict(os.environ,env,clear=True),patch.object(sam_memory_transport,'send',transport):
            for attempt in range(3):
                try:ns['commit_day']('2099-01-01');errors.append(False)
                except RuntimeError as exc:
                    errors.append(True);error_types.append(type(exc).__name__);error_messages.append(str(exc))
                if attempt==0 and 'new_need' in mode:remote['need']=True
                if attempt==0 and mode=='clear_receipt_failure_new_need':
                    with ns['connect']() as c:c.execute('DROP TRIGGER receipt_failure')
        ns['init_db']()
        with ns['connect']() as c:
            committed=bool(c.execute('SELECT committed FROM schedule_days').fetchone()[0])
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            states=[r[0] for r in c.execute('SELECT state FROM sam_memory_requests')]
        with receiver_connect() as c:
            receipts=c.execute('SELECT count(*) FROM sam_business_receipts').fetchone()[0]
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        held=mode in ('memory_lost','wrong_receipt','missing_config','history_lost','clear_lost_new_need','clear_false')
        assert committed!=held,(mode,errors)
        assert len(creates)==1 and len(clears)<=1
        assert len(set(posts))<=1 and receipts<=1
        if held:assert errors==[True]*3
        if mode=='memory_lost':
            assert len(posts)==1 and receipts==1 and states==['pending']
            assert error_types==['RuntimeError','MemoryHeld','MemoryHeld']
            assert all('different content' in e for e in error_messages[1:])
        if mode=='normal':assert len(posts)==1 and states==['confirmed']
        if mode=='wrong_receipt':assert states==['pending'] and receipts==1
        if mode in ('missing_config','history_lost','clear_lost_new_need','clear_false'):assert not posts
        if 'new_need' in mode:assert remote['need']
        results.append({'scenario':mode,'history_creates':len(creates),'clear_attempts':len(clears),'memory_attempts':len(posts),'receiver_commits':receipts,'local_committed':committed,'errors':errors,'recovery_gate':'FAIL: regenerated summary differs after history was posted' if mode=='memory_lost' else 'observed'})
print(json.dumps({'candidate_sha256':manifest,'cases':results,'candidate_acceptance':'FAILED','regression_reproduced':'Lost memory acknowledgment followed by changed generated history summary prevents retry','production_changes':False,'real_remote_calls':0,'limits':'Transport mocked; first-clear Odoo version race remains; full startup and deployment not proved.'}))
