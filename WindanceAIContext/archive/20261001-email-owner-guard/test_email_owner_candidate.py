"""Disposable HTTP/primitive/context checks; no production state or external I/O."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

with tempfile.TemporaryDirectory(prefix='windance-owner-candidate-') as temp:
    for name in ['DATA','LOG','CONFIG']:
        os.environ['AGENT_HARNESS_'+name+'_DIR']=temp
    os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=temp
    sys.path[:0]=['/Users/herald/services/email-owner-boundary-20261001','/Users/herald/services/agent-harness']
    import agent_harness as h
    import email_owner_boundary as boundary
    import httpx
    manifest=json.loads(Path('/Users/herald/services/email-owner-boundary-20261001/candidate-manifest.json').read_text())
    h.startup()
    h.save_email_report_refs('synthetic-william-report',[(1,'test',{'id':'synthetic-william-message','from':'sender@example.test','subject':'synthetic'})])
    effects=[]
    def denied(*args,**kwargs):raise AssertionError('External I/O forbidden')
    def approval(*args):effects.append('approval');return 'synthetic-approval'
    def delete(*args):effects.append('delete');return {}
    def rule(*args):effects.append('rule');return 'sender@example.test'
    http_results=[]
    async def main():
        with patch.object(h.urllib.request,'urlopen',side_effect=denied),patch.object(h.subprocess,'run',side_effect=denied),patch.object(h,'dispatch_staff_worker',side_effect=denied),patch.object(h,'model_reply',side_effect=denied),patch.object(h,'relevant_memory_text',return_value=''),patch.object(h,'upsert_vector_memory',return_value=None),patch.object(h,'request_approval',side_effect=approval),patch.object(h,'gmail_delete_message',side_effect=delete),patch.object(h,'upsert_email_sender_rule',side_effect=rule),patch.object(h,'auth_word_matches',side_effect=lambda text:text=='synthetic-auth-word'):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',4567)),base_url='http://test') as c:
                phrases=['delete 1','ALD 1','NOD 1','RED 1','save 1','reply to 1 saying synthetic','undo email 1','yes','no','send it','do not send it','approve abcd','always allow abcd','number 1 no approval','synthetic-auth-word','always delete all from example.test']
                for owner in ['Shawn','unknown-owner']:
                    for i,text in enumerate(phrases):
                        start=len(effects)
                        r=await c.post('/message',json={'user':owner,'channel':'vega-internal','message':text,'request_id':'synthetic-'+owner+'-'+str(i)})
                        assert r.json().get('model')=='mailbox-owner-denied',(owner,text,r.json().get('model'))
                        assert len(effects)==start,(owner,text,'unexpected effect')
                        http_results.append({'owner':owner,'case':i,'blocked':True})
                for text,wanted in [('delete 1',['approval']),('ALD 1',['rule','delete'])]:
                    start=len(effects)
                    r=await c.post('/message',json={'user':'William','channel':'vega-internal','message':text})
                    assert r.json().get('model')=='gmail-summary-actions'
                    assert effects[start:]==wanted,(text,effects[start:])
                # Forwarding carries original owner and never enters shared handlers.
                with patch.object(h.urllib.request,'urlopen',return_value=io.BytesIO(b'{"id":"synthetic-intake","status":"queued"}')) as opener:
                    r=await c.post('/message',json={'user':'Shawn','channel':'max-imessage','message':'delete 1','request_id':'synthetic-intake'})
                    assert r.json()['model']=='durable-receipt'
                    body=json.loads(opener.call_args.args[0].data);assert body['owner']=='Shawn' and body['id']=='synthetic-intake'
                # Ordinary business routing must not be stopped by eager email parsing.
                with patch.object(h,'odoo_status',return_value={'configured':True,'authenticated':True}),patch.object(h,'answer_odoo_question',return_value=('synthetic shared training','deterministic','synthetic-training')),patch.object(h,'odoo_training_schedule',return_value=('synthetic shared training','deterministic','synthetic-training')),patch.object(h,'orchestrate_general_request',return_value=('synthetic shared business','deterministic','synthetic-business')):
                    r=await c.post('/message',json={'user':'Shawn','channel':'vega-internal','message':'training schedule'})
                    assert r.json().get('reply') in ['synthetic shared training','synthetic shared business'], {'model':r.json().get('model'),'synthetic':r.json().get('reply','').startswith('synthetic')}
    asyncio.run(main())
    primitive_checks=0
    with patch.object(h.urllib.request,'urlopen',side_effect=denied),patch.object(h.subprocess,'run',side_effect=denied):
        for name in manifest['guarded_functions']:
            fn=getattr(h,name)
            args=[None for p in inspect.signature(fn).parameters.values() if p.default is inspect.Parameter.empty and p.kind in [p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD]]
            @boundary.bind_mailbox_owner
            def probe(payload):return fn(*args)
            assert probe(SimpleNamespace(user='Shawn'))['model']=='mailbox-owner-denied',name
            primitive_checks+=1
    # Legacy service context is unchanged, and concurrent scopes cannot leak owners.
    boundary.require_william_mailbox()
    barrier=threading.Barrier(2)
    @boundary.bind_mailbox_owner
    def concurrent(payload):
        barrier.wait(timeout=5);boundary.require_william_mailbox();return {'model':'allowed'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(concurrent,SimpleNamespace(user='William'));b=pool.submit(concurrent,SimpleNamespace(user='Shawn'))
        assert a.result()['model']=='allowed' and b.result()['model']=='mailbox-owner-denied'
    boundary.require_william_mailbox()
    print(json.dumps({'cross_owner_http_cases':len(http_results),'william_compatibility_cases':2,'sender_forwarding_preserved':True,'shared_business_route_preserved':True,'primitive_guard_checks':primitive_checks,'concurrent_scope_and_reset':True,'real_mailbox_calls':0,'model_calls':0,'production_modified':False}))


