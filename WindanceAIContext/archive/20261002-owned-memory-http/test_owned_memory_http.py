"""Mount candidate router on real Harness in disposable dirs; no outbound I/O."""
import asyncio
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch

async def test():
    with tempfile.TemporaryDirectory(prefix='windance-memory-http-') as directory:
        for name in ['DATA','LOG','CONFIG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=directory
        os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=directory
        sys.path.insert(0,'/Users/herald/services/agent-harness')
        import agent_harness as h
        import httpx
        import owned_fact_store as store
        from memory_ingress_policy import Policy,Resolver
        from owned_memory_api import make_router
        h.startup()
        database=Path(directory)/'owned-fixture.db'
        def connect():return sqlite3.connect(database,timeout=10)
        c=connect();store.install(c);c.close()
        policies=[Policy(owner,'fixture-'+owner,frozenset((owner,'fixture','personal',op) for op in ['read','write','delete'])) for owner in ['william','shawn']]
        h.app.include_router(make_router(connect,Resolver(policies),lambda value:not h.memory_looks_secret(value)))
        def denied(*args,**kwargs):raise AssertionError('Outbound I/O forbidden')
        with patch.object(h.urllib.request,'urlopen',side_effect=denied),patch.object(h.subprocess,'run',side_effect=denied),patch.object(h,'model_reply',side_effect=denied),patch.object(h,'dispatch_staff_worker',side_effect=denied):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',4567)),base_url='http://fixture') as client:
                body={'event_id':'fixture-one','owner':'william','channel':'fixture','scope':'personal','kind':'preference','key':'same','value':'synthetic habit','expected_revision':0}
                async def write(payload=body,owner='william'):
                    return await client.post('/memory/owned/facts',json=payload,headers={'Authorization':'Bearer fixture-'+owner})
                response=await client.post('/memory/owned/facts',json=body)
                assert response.status_code==403 # Trusted loopback cannot bypass route policy.
                assert (await write(owner='shawn')).status_code==403
                responses=await asyncio.gather(*(write() for _ in range(8)))
                assert all(r.status_code==200 for r in responses)
                receipts=[r.json()['receipt'] for r in responses]
                assert sum(not r['replayed'] for r in receipts)==1 and all(r['revision']==1 for r in receipts)
                assert (await write({**body,'value':'conflicting retry'})).status_code==409
                q={'owner':'shawn','channel':'fixture','scope':'personal'}
                response=await client.post('/memory/owned/query',json=q,headers={'Authorization':'Bearer fixture-shawn'})
                assert response.json()=={'facts':[]}
                changed={**body,'event_id':'fixture-two','value':'corrected habit','expected_revision':1}
                assert (await write(changed)).status_code==200
                response=await write();assert response.json()['receipt']['superseded'] is True
                deleted={**body,'event_id':'fixture-three','value':None,'operation':'delete','expected_revision':2}
                assert (await write(deleted)).status_code==200
                response=await client.post('/memory/owned/query',json={**q,'owner':'william'},headers={'Authorization':'Bearer fixture-william'})
                assert response.json()=={'facts':[]}
                secret={**body,'event_id':'fixture-secret','key':'different','value':'password: SYNTHETIC_SECRET_DO_NOT_STORE'}
                response=await write(secret)
                assert response.status_code==422 and 'SYNTHETIC_SECRET' not in response.text
        with connect() as c:
            assert c.execute('SELECT count(*) FROM owned_fact_requests').fetchone()[0]==3
            assert c.execute('SELECT count(*) FROM owned_fact_events').fetchone()[0]==3
        print(json.dumps({'real_harness_router_mounted_in_disposable_process':True,'concurrent_identical_requests':8,
          'single_committed_initial_write':True,'loopback_without_scoped_credential_denied':True,'forged_owner_denied':True,
          'cross_owner_query_empty':True,'correction_delete_replay_passed':True,'actual_secret_classifier_rejected_fixture':True,
          'real_sends':0,'model_calls':0,'production_writes':0,'limits':'In-process ASGI, synthetic credentials; no production mounting or natural caller integration'}))

asyncio.run(test())
