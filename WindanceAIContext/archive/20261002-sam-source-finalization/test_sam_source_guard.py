"""Actual SAM schema, source mutation coverage and SQLite writer exclusion."""
import ast,hashlib,json,sqlite3,tempfile,threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
import sam_source_guard as guard
root=Path(__file__).parent/'sam-memory-r4-private'
source=(root/'sam_schedule.memory-r4.private.py').read_text(encoding='utf-8')
assert hashlib.sha256(source.encode()).hexdigest()=='db71ccb2da8f794ba21f0fb1cf74995890acf8bbb94c436b680dc76e630ee816'
nodes=[n for n in ast.parse(source).body if getattr(n,'name','')=='init_db'];assert len(nodes)==1
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
results=[]
for mode in ('normal','item_edit','item_delete','carry_edit','suppression_edit','receipt_mismatch','writer_exclusion'):
    with tempfile.TemporaryDirectory(prefix='sam-source-guard-') as directory:
        folder=Path(directory)
        def connect():
            c=sqlite3.connect(folder/'sam.db',timeout=0.1,factory=ClosingConnection);c.row_factory=sqlite3.Row;return c
        import sys
        sys.path.insert(0,str(root))
        ns={'Any':Any,'connect':connect,'DEFAULT_TRAINERS':[],'now_iso':lambda:'fixture'}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-schema>','exec'),ns);ns['init_db']()
        with connect() as c:
            c.execute("INSERT INTO schedule_days(date,day_name) VALUES('2099-01-01','fixture')")
            c.execute("INSERT INTO schedule_items(id,date,horse_key,horse_name,training_raw,updated_at) VALUES('fixture','2099-01-01','fixture','SYNTHETIC','A','fixture')")
        with connect() as c:expected=guard.source_token(c,'2099-01-01')
        receipt={'status':'ok','event_id':'synthetic-confirmed-event'}
        if mode=='item_edit':
            with connect() as c:c.execute("UPDATE schedule_items SET training_raw='B'")
        if mode=='item_delete':
            with connect() as c:c.execute('DELETE FROM schedule_items')
        if mode=='carry_edit':
            with connect() as c:c.execute("INSERT INTO missed_training(id,missed_date,target_date,horse_key,horse_name,training_code,status,detail_json,created_at,updated_at) VALUES('fixture','2098-12-31','2099-01-01','fixture','SYNTHETIC','A','local_carried','{}','fixture','fixture')")
        if mode=='suppression_edit':
            with connect() as c:c.execute("INSERT INTO carryover_suppressions(date,horse_key,training_code,reason,created_at) VALUES('2099-01-01','fixture','A','fixture','fixture')")
        if mode=='receipt_mismatch':
            guard.finalize(connect,'2099-01-01',expected,receipt,'fixture');receipt={'status':'ok','event_id':'other'}
        writer=[]
        original=guard.source_token
        def checked(db,date_key):
            token=original(db,date_key)
            def mutate():
                try:
                    with connect() as c:c.execute("UPDATE schedule_items SET training_raw='B'")
                    writer.append('unexpected_write')
                except sqlite3.OperationalError as exc:
                    assert 'locked' in str(exc);writer.append('locked')
            t=threading.Thread(target=mutate);t.start();t.join(2);assert not t.is_alive()
            return token
        held=False
        try:
            if mode=='writer_exclusion':
                with patch.object(guard,'source_token',checked):guard.finalize(connect,'2099-01-01',expected,receipt,'fixture')
            else:guard.finalize(connect,'2099-01-01',expected,receipt,'fixture')
        except guard.SourceChanged:held=True
        assert held==(mode not in ('normal','writer_exclusion'))
        if mode=='normal':assert guard.finalize(connect,'2099-01-01',expected,receipt,'fixture')['already_committed']
        if mode=='writer_exclusion':assert writer==['locked']
        with connect() as c:
            committed=bool(c.execute('SELECT committed FROM schedule_days').fetchone()[0])
            assert committed==(mode in ('normal','writer_exclusion','receipt_mismatch'))
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        results.append({'scenario':mode,'held':held,'writer_exclusion_verified':mode=='writer_exclusion'})
print(json.dumps({'cases':results,'production_changes':False,'full_candidate_integrated':False,'limits':'Initial coherent snapshot and after-rollover token capture must still be integrated; conservative all-carry dependency; subsequent edits need invalidation/correction workflow.'}))
