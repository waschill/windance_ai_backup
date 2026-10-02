"""Concurrent receipts, correction conflict, old replay and consistent cold restore."""
import concurrent.futures,json,secrets,sqlite3,tempfile
from pathlib import Path
from sam_business_memory import record,SCHEMA,SourceConflict
from sam_memory_contract import ProducerDenied
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);path=root/'fixture.db';token=secrets.token_urlsafe(32)
    def connect():return sqlite3.connect(path,timeout=3)
    with connect() as c:c.executescript(SCHEMA)
    c.close()
    body={'kind':'sam_daily_schedule','key':'2026-10-01','value':'Synthetic original report','confidence':0.92,'source':'SAM schedule display'}
    def save(event='event-a',rev=0,payload=body,auth=None):
        return record(connect,auth or 'Bearer '+token,token,payload,event_id=event,expected_revision=rev,validate_content=lambda _:True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:receipts=list(pool.map(lambda _:save(),range(8)))
    assert sum(not r['replayed'] for r in receipts)==1 and all(r['revision']==1 for r in receipts)
    newer={**body,'value':'Synthetic corrected report'}
    try:save(payload=newer)
    except SourceConflict:pass
    else:raise AssertionError('Changed same event accepted')
    second=save('event-b',1,newer);assert second['revision']==2
    replay=save();assert replay['replayed'] and replay['superseded'] and replay['revision']==1
    try:save('stale-event',0,newer)
    except SourceConflict:pass
    else:raise AssertionError('Stale revision accepted')
    try:save('unauthorized',2,newer,'Bearer invalid')
    except ProducerDenied:pass
    else:raise AssertionError('Wrong credential accepted')
    # Inject receipt failure: the source correction must roll back with it.
    with connect() as c:
        c.execute("CREATE TRIGGER refuse_receipt BEFORE INSERT ON sam_business_receipts BEGIN SELECT RAISE(ABORT,'synthetic'); END")
    c.close()
    try:save('failed-event',2,{**body,'value':'Should not persist'})
    except sqlite3.IntegrityError:pass
    else:raise AssertionError('Injected failure missing')
    with connect() as c:
        assert c.execute('SELECT revision,summary FROM sam_business_sources').fetchone()==(2,newer['value'])
        assert c.execute('SELECT count(*) FROM sam_business_receipts').fetchone()[0]==2
        c.execute('DROP TRIGGER refuse_receipt')
    c.close()
    original=connect();cold=sqlite3.connect(root/'cold.db');original.backup(cold);cold.close();original.close()
    path=root/'cold.db';restored=save();assert restored==replay
    with connect() as c:c.execute("UPDATE sam_business_sources SET summary='Synthetic drift'")
    c.close()
    try:save()
    except SourceConflict:pass
    else:raise AssertionError('Source drift accepted')
    print(json.dumps({'concurrent_requests':8,'new_commits':1,'correction_revision':2,
                      'old_replay_superseded':True,'stale_and_changed_requests_denied':True,
                      'receipt_failure_rolled_back_source':True,'cold_replay_equal':True,'source_drift_denied':True,
                      'external_calls':0,'production_changes':False}))
