"""Probe real SAM schedule reader and rollover composition without live services."""
import ast,datetime as dt,hashlib,json,os,secrets,sqlite3,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
import sam_business_memory as receiver
root=Path(__file__).parent/'sam-memory-r4-private'
manifest=json.loads((root/'memory-r4-manifest.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
sys.path.insert(0,str(root))
import sam_commit_snapshot,sam_memory_transport
names={'connect','init_db','get_schedule','effective_active_carryovers','record_missed_training','rollover_unfinished_training','post_completed_service_history','commit_day','post_sam_business_memory'}
nodes=[n for n in ast.parse((root/'sam_schedule.memory-r4.private.py').read_text(encoding='utf-8')).body if getattr(n,'name','') in names]
assert len(nodes)==len(names)
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
def connect(*a,**kw):return sqlite3.connect(*a,**kw,factory=ClosingConnection)
results=[]
for mode in ('new_carry_lost','existing_carry_lost','before_freeze_crash','edit_during_send'):
    with tempfile.TemporaryDirectory(prefix='sam-rollover-r4-') as directory:
        folder=Path(directory);posts=[];errors=[];credential=secrets.token_hex(24)
        ns={'Any':Any,'sqlite3':SimpleNamespace(connect=connect,Connection=sqlite3.Connection,Row=sqlite3.Row),'dt':dt,'json':json,
            'DATA_DIR':folder,'DB_PATH':folder/'sam.db','DEFAULT_TRAINERS':[],'now_iso':lambda:'2099-01-01T00:00:00',
            'selected_date':lambda date:(date,'fixture',None),'trainer_rows':lambda **k:[],
            'ACTIVE_CARRY_STATUSES':{'carried','local_carried','already_present','conflict','error'},'HERALD_BASE':'http://fixture.invalid',
            'ROLLOVER_UNFINISHED_TRAINING':True,'log_event':lambda *a,**k:None}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-rollover-r4>','exec'),ns);ns['init_db']()
        with ns['connect']() as c:
            c.execute("INSERT INTO schedule_days(date,day_name) VALUES('2099-01-01','fixture')")
            c.execute("INSERT INTO schedule_items(id,date,horse_key,horse_name,odoo_schedule_row_id,training_raw,updated_at) VALUES('fixture','2099-01-01','fixture','SYNTHETIC',1,'A','fixture')")
        if mode=='existing_carry_lost':
            ns['record_missed_training']('2098-12-31','2099-01-01',{'horse_key':'fixture','horse_name':'SYNTHETIC','training_raw':'B','odoo_schedule_row_id':1},'local_carried',{})
        def receiver_connect():return connect(folder/'receiver.db')
        with receiver_connect() as c:c.executescript(receiver.SCHEMA)
        def transport(url,path,envelope):
            posts.append(envelope)
            result=receiver.record(receiver_connect,'Bearer '+credential,credential,envelope['payload'],event_id=envelope['event_id'],expected_revision=envelope['expected_revision'],validate_content=lambda _:True)
            if mode.endswith('_lost') and len(posts)==1:raise RuntimeError('synthetic response loss')
            if mode=='edit_during_send':
                with ns['connect']() as c:c.execute("UPDATE schedule_items SET training_raw='CHANGED' WHERE id='fixture'")
            return result
        original_freeze=sam_commit_snapshot.freeze;freezes=[]
        def freeze(*a,**kw):
            freezes.append(1)
            if mode=='before_freeze_crash' and len(freezes)==1:raise RuntimeError('synthetic stop before freeze')
            return original_freeze(*a,**kw)
        env={'SAM_BUSINESS_MEMORY_URL':'https://fixture.invalid','SAM_BUSINESS_MEMORY_CREDENTIAL_FILE':'fixture-only'}
        with patch.dict(os.environ,env,clear=True),patch.object(sam_memory_transport,'send',transport),patch.object(sam_commit_snapshot,'freeze',freeze):
            for attempt in range(2):
                try:ns['commit_day']('2099-01-01');errors.append(None)
                except RuntimeError as exc:errors.append(type(exc).__name__)
        with ns['connect']() as c:
            committed=bool(c.execute('SELECT committed FROM schedule_days').fetchone()[0])
            carries=c.execute('SELECT count(*) FROM missed_training').fetchone()[0]
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        if mode=='new_carry_lost':assert committed and len(posts)==2 and carries==1
        if mode=='existing_carry_lost':assert not committed and errors==['RuntimeError','SnapshotHeld'] and len(posts)==1 and carries==2
        if mode=='before_freeze_crash':assert committed and carries==1 and 'Carried to 2099-01-02: 0' in posts[0]['payload']['value']
        if mode=='edit_during_send':assert committed and 'CHANGED' not in posts[0]['payload']['value']
        results.append({'scenario':mode,'committed':committed,'memory_attempts':len(posts),'carry_rows':carries,'errors':errors,
            'gate':'pass' if mode=='new_carry_lost' else 'FAIL: existing carry mutation blocks own retry' if mode=='existing_carry_lost' else 'FAIL: pre-freeze crash omits earlier carry effect' if mode=='before_freeze_crash' else 'FAIL: changed schedule marked committed to stale summary'})
print(json.dumps({'candidate_main_sha256':manifest['sam_schedule.memory-r4.private.py'],'cases':results,'candidate_acceptance':'FAILED','production_changes':False,'real_remote_calls':0}))
