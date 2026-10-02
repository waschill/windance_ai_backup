"""Durable restart reconciliation and stop receipt ordering without worker effects."""
import json,tempfile
from pathlib import Path
from diagnostic_job_api import Submission
from diagnostic_job_ledger import Ledger
import diagnostic_consumer as consumer

with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'jobs.db';ledger=Ledger(path)
    def submit(name):return ledger.submit('owner',Submission(request_key=name,kind='email_payload_diagnosis',evidence_sha256='a'*64))['id']
    first,second=submit('first'),submit('second');calls=[]
    def lost(ledger,key,*args):
        calls.append(('run',key));assert ledger.claim(key);raise RuntimeError('PRIVATE_TRANSPORT_SENTINEL')
    def unresolved(*args,**kwargs):calls.append(('reconcile',kwargs.get('mode')));raise RuntimeError('uncertain')
    consumer.run_once=lost;consumer.collect=unresolved
    result=consumer.run_cycle(ledger,'b'*64,'c'*64)
    assert result['state']=='held' and 'PRIVATE' not in json.dumps(result)
    # A new ledger instance sees persisted uncertainty and only queries the original job.
    restarted=Ledger(path)
    assert consumer.run_cycle(restarted,'b'*64,'c'*64)['state']=='held'
    assert calls==[('run',first),('reconcile','reconcile')]
    assert restarted.request(second)[1]=='queued'
    def confirmed(ledger,key,*args,**kwargs):
        assert key==first and kwargs['mode']=='reconcile'
        ledger.finish(key,{'job_id':key,'evidence_sha256':'a'*64,'worker_stopped':True,'outcome':'completed'})
        return {'started':False,'state':'completed'}
    consumer.collect=confirmed
    assert consumer.run_cycle(restarted,'b'*64,'c'*64)['state']=='completed'
    assert restarted.request(second)[1]=='queued'
    assert restarted.claim(second);restarted.cancel('owner',second)
    consumer.cancel_once=lambda *args:{'job_id':'wrong','worker_stopped':True,'stop_acknowledged':True}
    assert consumer.run_cycle(restarted,'b'*64,'c'*64)['state']=='held'
    assert restarted.request(second)[1]=='cancel_requested'
    consumer.cancel_once=lambda *args:{'job_id':second,'evidence_sha256':'a'*64,'worker_stopped':True,'stop_acknowledged':True}
    assert consumer.run_cycle(restarted,'b'*64,'c'*64)['state']=='cancelled'
    assert consumer.run_cycle(restarted,'b'*64,'c'*64)['state']=='idle'
    print(json.dumps({'passed':True,'restart_reconciles_without_run':True,'no_next_job_on_uncertainty':True,'matching_stop_required':True,'worker_calls':0}))
