"""Actual installed legacy HTTP memory routes, synthetic DB and service credential only."""
import asyncio,hashlib,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch

async def main():
    with tempfile.TemporaryDirectory(prefix='legacy-memory-boundary-') as directory:
        for name in ['DATA','LOG','CONFIG']:os.environ['AGENT_HARNESS_'+name+'_DIR']=directory
        os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=directory
        sys.path.insert(0,'/Users/herald/services/agent-harness')
        import agent_harness as h,httpx,email_owner_boundary
        h.startup();h.HARNESS_TOKEN='fixture-service-token'
        with h.db() as c:
            c.execute('INSERT INTO memories(kind,key,value,confidence,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                      ('preference','fixture-private','WILLIAM_PRIVATE_FIXTURE',1,'fixture-william','fixture-time','fixture-time'))
            c.commit()
        def forbidden(*args,**kwargs):raise AssertionError('External operation forbidden')
        context=email_owner_boundary._owner.set('shawn')
        try:
            with patch.object(h.urllib.request,'urlopen',side_effect=forbidden),patch.object(h.subprocess,'run',side_effect=forbidden),\
                 patch.object(h,'model_reply',side_effect=forbidden),patch.object(h,'upsert_vector_memory',return_value=None),\
                 patch.object(h,'mirror_to_hermes_memory',return_value=None):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',4567)),base_url='http://fixture') as client:
                    headers={'Authorization':'Bearer fixture-service-token'}
                    read=await client.get('/memory',headers=headers)
                    assert read.status_code==200 and any(r['value']=='WILLIAM_PRIVATE_FIXTURE' for r in read.json()['items'])
                    write=await client.post('/memory',headers=headers,json={'kind':'preference','key':'fixture-private',
                          'value':'OVERWRITTEN_FIXTURE','confidence':1,'source':'fixture-unverified-owner'})
                    assert write.status_code==200
                    with h.db() as c:
                        assert c.execute("SELECT value FROM memories WHERE key='fixture-private'").fetchone()[0]=='OVERWRITTEN_FIXTURE'
        finally:email_owner_boundary._owner.reset(context)
    print(json.dumps({'installed_harness_sha256':hashlib.sha256(Path(h.__file__).read_bytes()).hexdigest(),
        'actual_legacy_http_get_not_filtered_by_owner_context':True,
        'actual_legacy_http_post_can_overwrite_same_unscoped_key':True,
        'credential':'synthetic shared service credential','private_data_used':False,'production_changes':False,
        'model_calls':0,'sends':0,'limits':'Controlled fixture, not historical disclosure or unauthenticated network access proof; vector/mirror writes intercepted'}))
asyncio.run(main())
