"""One bounded operator cycle over durable jobs; no daemon or scheduler installation."""
from diagnostic_remote_adapter import run_once,collect,cancel_once

def run_cycle(ledger,worker_hash,launcher_hash):
    with ledger.connect() as connection:
        active=connection.execute("SELECT id,state FROM jobs WHERE state IN ('running','cancel_requested') ORDER BY rowid LIMIT 2").fetchall()
        if len(active)>1:
            return {'started':False,'state':'held','reason':'multiple_active_jobs'}
        candidate=active[0] if active else connection.execute("SELECT id,state FROM jobs WHERE state='queued' ORDER BY rowid LIMIT 1").fetchone()
    if candidate is None:return {'started':False,'state':'idle'}
    key,state=candidate['id'],candidate['state']
    try:
        if state=='cancel_requested':
            receipt=cancel_once(ledger,key,worker_hash)
            result=ledger.acknowledge_cancel(key,receipt)
            return {'started':False,'state':result['state'],'job_id':key}
        if state=='running':
            result=collect(ledger,key,worker_hash,launcher_hash,mode='reconcile')
        else:
            result=run_once(ledger,key,worker_hash,launcher_hash)
        return {**result,'job_id':key}
    except Exception:
        # No replay, requeue, next-job fallback or untrusted exception text.
        return {'started':None,'state':'held','reason':'outcome_unconfirmed','job_id':key}
