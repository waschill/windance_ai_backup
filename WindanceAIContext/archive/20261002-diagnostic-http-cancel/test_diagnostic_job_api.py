"""Actual ASGI authentication and SQLite concurrency/recovery; no dispatch."""
import concurrent.futures,hashlib,json,secrets,sqlite3,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from diagnostic_job_api import create_app
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);tokens=[secrets.token_urlsafe(32) for _ in range(2)]
    config={hashlib.sha256(t.encode()).hexdigest():p for t,p in zip(tokens,['principal-a','principal-b'])}
    headers=[{'Authorization':'Bearer '+t} for t in tokens]
    app=create_app(root/'jobs.db',config);client=TestClient(app)
    body={'request_key':'fixture','kind':'email_payload_diagnosis','evidence_sha256':'a'*64}
    assert client.post('/jobs',json=body).status_code==401
    assert client.post('/jobs',json=body,headers={'Authorization':'Bearer invalid'}).status_code==401
    assert client.post('/jobs',json={**body,'owner':'principal-b'},headers=headers[0]).status_code==422
    first=client.post('/jobs',json=body,headers=headers[0]);assert first.status_code==200
    key=first.json()['id'];assert first.json()['state']=='queued'
    again=client.post('/jobs',json=body,headers=headers[0]).json();assert again['id']==key and again['reused']
    assert client.post('/jobs',json={**body,'evidence_sha256':'b'*64},headers=headers[0]).status_code==409
    for method,path in [('get',f'/jobs/{key}'),('get',f'/jobs/{key}/result'),('post',f'/jobs/{key}/cancel')]:
        assert getattr(client,method)(path,headers=headers[1]).status_code==404
    other=client.post('/jobs',json=body,headers=headers[1]).json();assert other['id']!=key
    cancelled=client.post('/jobs/'+other['id']+'/cancel',headers=headers[1]).json();assert cancelled['state']=='cancelled'
    assert app.state.ledger.claim(other['id']) is False
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        claimed=list(pool.map(app.state.ledger.claim,[key,key]))
    assert sorted(claimed)==[False,True]
    pending=client.post('/jobs/'+key+'/cancel',headers=headers[0]).json()
    assert pending['state']=='cancel_requested' and pending['worker_stopped'] is False
    def failed_stop(*a):raise RuntimeError('PRIVATE_PROVIDER_SENTINEL')
    failedclient=TestClient(create_app(root/'jobs.db',config,cancel_adapter=failed_stop))
    failedreply=failedclient.post('/jobs/'+key+'/cancel',headers=headers[0])
    assert failedreply.json()['state']=='cancel_requested' and failedreply.json()['worker_stopped'] is False
    assert 'PRIVATE_PROVIDER_SENTINEL' not in failedreply.text
    wrongclient=TestClient(create_app(root/'jobs.db',config,cancel_adapter=lambda *a:{'job_id':'wrong','worker_stopped':True,'stop_acknowledged':True}))
    assert wrongclient.post('/jobs/'+key+'/cancel',headers=headers[0]).json()['state']=='cancel_requested'
    with sqlite3.connect(root/'jobs.db') as original,sqlite3.connect(root/'cold.db') as cold:original.backup(cold)
    recovered=create_app(root/'cold.db',config);coldclient=TestClient(recovered)
    retry=coldclient.post('/jobs',json=body,headers=headers[0]).json()
    assert retry['id']==key and retry['state']=='cancel_requested'
    assert recovered.state.ledger.claim(key) is False
    assert coldclient.get('/jobs/'+key+'/result',headers=headers[0]).status_code==409
    assert 'worker_liveness' in coldclient.get('/jobs/'+key,headers=headers[0]).json()
    print(json.dumps({'passed':['authentication','body_owner_rejected','same_request_reused','changed_request_conflict','cross_principal_denied','queued_cancel','concurrent_single_claim','running_cancel_not_completion','failed_stop_remains_pending','wrong_stop_identity_rejected','cold_retry_no_requeue','no_false_result'],'dispatch_calls':0}))
