"""SQLite concurrent admission and cold uncertainty; no worker execution."""
import concurrent.futures,json,sqlite3,tempfile
from pathlib import Path
from diagnostic_job_ledger import Ledger,JobError
from diagnostic_job_api import Submission
def body(key):return Submission(request_key=str(key),kind='email_payload_diagnosis',evidence_sha256='a'*64)
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'jobs.db';ledger=Ledger(path)
    def submit(i):
        try:return Ledger(path).submit('one',body(i))
        except JobError as error:assert error.status_code==429;return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(submit,range(20)))
    accepted=[r for r in results if r];assert len(accepted)==8
    # Exact idempotent requests remain inspectable even when admission is full.
    original=next(i for i,r in enumerate(results) if r)
    assert ledger.submit('one',body(original))['id']==results[original]['id']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:claims=list(pool.map(ledger.claim,[r['id'] for r in accepted]))
    assert sum(claims)==1
    running=accepted[claims.index(True)]['id']
    ledger.cancel('one',running)
    assert ledger.request(running)[1]=='cancel_requested'
    pending=next(r['id'] for r in accepted if r['id']!=running)
    assert ledger.claim(pending) is False
    with sqlite3.connect(path) as source,sqlite3.connect(Path(directory)/'cold.db') as target:source.backup(target)
    cold=Ledger(Path(directory)/'cold.db');assert cold.claim(pending) is False
    # A matching explicit stop receipt, not elapsed time or restart, releases running capacity.
    ledger.acknowledge_cancel(running,{'job_id':running,'evidence_sha256':'a'*64,'worker_stopped':True,'stop_acknowledged':True})
    assert ledger.claim(pending) is True
    # One cancelled job frees owner admission; global capacity remains bounded.
    assert ledger.submit('one',body('replacement'))['state']=='queued'
    for owner in ('two','three','four'):
        for i in range(8):ledger.submit(owner,body(i))
    try:ledger.submit('five',body(0));raise AssertionError('global ceiling missing')
    except JobError as error:assert error.status_code==429
    with ledger.connect() as c:
        active=c.execute("select count(*) from jobs where state in ('queued','running','cancel_requested')").fetchone()[0]
        assert active==32
    print(json.dumps({'passed':True,'concurrent_owner_limit':8,'global_active_limit':32,'running_limit':1,'cold_uncertainty_holds_capacity':True,'worker_calls':0}))
