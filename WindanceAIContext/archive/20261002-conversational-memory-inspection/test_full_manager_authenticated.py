"""Full staged manager app, actual middleware/routes; no worker lifecycle or live I/O."""
import ast,asyncio,json,os,tempfile
from pathlib import Path
from aiohttp.test_utils import TestClient,TestServer
from authenticated_message_ingress import authenticated_source_loader

async def main():
    root=Path(__file__).resolve().parent
    candidate=ast.parse((root/'manager-authenticated-candidate.private.py').read_text())
    # Replace only private token loading for fixture execution; never read real token.
    tokens=[n for n in candidate.body if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='TOKEN' for x in n.targets)]
    assert len(tokens)==1
    tokens[0].value=ast.Constant('fixture-unused-harness-token');ast.fix_missing_locations(candidate)
    with tempfile.TemporaryDirectory(prefix='full-manager-intake-') as directory:
        base=Path(directory)
        os.environ['VEGA_MANAGER_DATA']=str(base/'manager')
        os.environ.pop('VEGA_AUTHENTICATED_INTAKE_CONFIG',None)
        scope={'__name__':'isolated_manager'}
        exec(compile(candidate,'<private-manager-candidate>','exec'),scope)
        def forbidden(*args,**kwargs):raise AssertionError('External manager operation forbidden')
        scope['http']=forbidden;scope['send']=forbidden
        scope['init']()
        disabled=scope['app']()
        assert not any(str(r.resource.canonical)=='/messages/authenticated' for r in disabled.router.routes())
        config=base/'adapter.json'
        config.write_text(json.dumps({'issuer':'fixture-sal','credential':'fixture-adapter-only','owners':['william','shawn']}));config.chmod(0o600)
        os.environ['VEGA_AUTHENTICATED_INTAKE_CONFIG']=str(config)
        app=scope['app']()
        assert len(app.cleanup_ctx)==1
        app.cleanup_ctx.clear() # Explicit isolation: no loop/dispatch/sender starts.
        async with TestClient(TestServer(app)) as client:
            assert (await client.get('/health')).status==200
            payload={'owner':'william','source_id':'max-imessage:7001','message':'remember this: synthetic full-app preference'}
            headers={'Authorization':'Bearer fixture-adapter-only'}
            assert (await client.post('/messages/authenticated',json=payload)).status==403
            first=await client.post('/messages/authenticated',json=payload,headers=headers)
            assert first.status==202
            receipt=await first.json();assert receipt['id']=='max-imessage:7001'
            retry=await client.post('/messages/authenticated',json=payload,headers=headers)
            assert (await retry.json())['replayed'] is True
            source=authenticated_source_loader(scope['connect'])('william',receipt['source_ref'])
            assert source.text==payload['message']
            secret={**payload,'source_id':'max-imessage:7002','message':'Vega, remember for business: password SYNTHETIC_REJECTED'}
            rejected=await client.post('/messages/authenticated',json=secret,headers=headers)
            assert rejected.status==422 and 'SYNTHETIC_REJECTED' not in await rejected.text()
            assert (await client.post('/messages/authenticated',json={**payload,'session':'shawn'},headers=headers)).status==422
            with scope['connect']() as c:
                assert c.execute('SELECT count(*) FROM messages').fetchone()[0]==1
                assert c.execute('SELECT count(*) FROM authenticated_message_sources').fetchone()[0]==1
                assert c.execute('SELECT count(*) FROM projects').fetchone()[0]==0
                assert c.execute('SELECT status FROM messages').fetchone()[0]=='memory_pending'
            delivery_calls=[]
            async def fixture_send(answer,mid,owner):
                assert owner==('Shawn' if mid=='max-imessage:7301' else 'William');delivery_calls.append(mid);return {'fixture_only':True}
            scope['send']=fixture_send
            await scope['process_messages']()
            with scope['connect']() as c:
                fact=c.execute('SELECT fact_key,revision,value FROM owned_facts').fetchone()
                key=fact[0];assert fact[1]==1 and fact[2]=='synthetic full-app preference'
            async def memory_request(row,text):
                response=await client.post('/messages/authenticated',json={**payload,'source_id':'max-imessage:'+str(row),'message':text},headers=headers)
                assert response.status==202
                await scope['process_messages']()
            await memory_request(7101,f'correct memory {key} revision 1: revised synthetic preference')
            await memory_request(7102,f'correct memory {key} revision 1: stale attempted replacement')
            with scope['connect']() as c:
                assert tuple(c.execute('SELECT revision,value FROM owned_facts').fetchone())==(2,'revised synthetic preference')
                assert 'Nothing was overwritten' in c.execute("SELECT answer FROM messages WHERE id='max-imessage:7102'").fetchone()[0]
            await memory_request(7103,f'forget memory {key} revision 2')
            await memory_request(7104,'forget everything')
            with scope['connect']() as c:
                assert tuple(c.execute('SELECT revision,value,deleted FROM owned_facts').fetchone())==(3,None,1)
                assert c.execute("SELECT count(*) FROM messages WHERE status='answered'").fetchone()[0]==5
                c.execute("UPDATE messages SET status='memory_pending' WHERE id='max-imessage:7001'")
            scope['MEMORY_PROCESSOR'].process_pending()
            with scope['connect']() as c:
                assert c.execute('SELECT deleted FROM owned_facts').fetchone()[0]==1
                assert 'newer revision' in c.execute("SELECT answer FROM messages WHERE id='max-imessage:7001'").fetchone()[0]
            assert len(delivery_calls)==5
            await memory_request(7201,'remember for business: BUSINESS_ONLY_FIXTURE')
            other=await client.post('/messages/authenticated',json={'owner':'shawn','source_id':'max-imessage:7301',
                'message':'remember this: SHAWN_ONLY_FIXTURE'},headers=headers)
            assert other.status==202
            await scope['process_messages']()
            await memory_request(7202,'remember this: WILLIAM_ONLY_FIXTURE')
            await memory_request(7203,'What do you remember about me?')
            await memory_request(7204,'show my business memories')
            with scope['connect']() as c:
                personal=c.execute("SELECT answer FROM messages WHERE id='max-imessage:7203'").fetchone()[0]
                business=c.execute("SELECT answer FROM messages WHERE id='max-imessage:7204'").fetchone()[0]
                assert 'WILLIAM_ONLY_FIXTURE' in personal
                assert all(value not in personal for value in ['SHAWN_ONLY_FIXTURE','BUSINESS_ONLY_FIXTURE','revised synthetic preference'])
                assert 'BUSINESS_ONLY_FIXTURE' in business and 'WILLIAM_ONLY_FIXTURE' not in business
                c.execute("UPDATE messages SET request='changed fixture source' WHERE id='max-imessage:7202'")
            await memory_request(7205,'show my personal memories')
            with scope['connect']() as c:
                answer=c.execute("SELECT answer FROM messages WHERE id='max-imessage:7205'").fetchone()[0]
                assert 'No current source-verified' in answer and 'WILLIAM_ONLY_FIXTURE' not in answer
            for row,text in [(7003,'approve SYNTHETICCONTROL to all'),
                             (7004,'CONFIRM LEVEL 8 SHUTDOWN SYNTHETICLEVEL')]:
                response=await client.post('/messages/authenticated',json={**payload,'source_id':'max-imessage:'+str(row),'message':text},headers=headers)
                assert response.status==202
                result=await response.json()
                retained=authenticated_source_loader(scope['connect'])('william',result['source_ref']).text
                assert 'SYNTHETIC' not in retained and 'REDACTED' in retained
            blocked=await client.post('/messages/authenticated',json={**payload,'source_id':'max-imessage:7005',
                'message':'remember this: approve SYNTHETICMEMORY'},headers=headers)
            assert blocked.status==422
            with scope['connect']() as c:
                assert c.execute('SELECT count(*) FROM messages').fetchone()[0]==13
                retained=' '.join(row[0] for row in c.execute('SELECT request FROM messages'))
                assert all(value not in retained for value in ['SYNTHETICCONTROL','SYNTHETICLEVEL','SYNTHETICMEMORY'])
        config.chmod(0o644)
        try:scope['app']()
        except ValueError:pass
        else:raise AssertionError('World-readable credential config accepted')
        config.chmod(0o600)
        config.write_text('{invalid')
        try:scope['app']()
        except ValueError:pass
        else:raise AssertionError('Malformed configured policy accepted')
    print(json.dumps({'full_candidate_manager_http_and_middleware':True,'background_lifecycle_disabled':True,
        'synthetic_token_substituted_before_module_execution':True,'optional_configuration_and_fail_closed_validation':True,
        'actual_policy_rejection_before_source_storage':True,'stable_authenticated_source_and_retry':True,
        'installed_control_redactors_before_storage':True,'redacted_memory_request_refused':True,
        'actual_message_processor_learn_correct_forget_without_worker':True,
        'stale_revision_refused_and_recovery_retry_no_resurrection':True,
        'ambiguous_forget_held_without_worker':True,'delivery_calls_intercepted':True,
        'conversational_owner_scoped_inspection':True,'business_personal_separated':True,
        'changed_source_and_forgotten_facts_withheld':True,
        'production_changes':False,'model_calls':0,'sends':0,'dispatches':0,
        'limits':'Synthetic sources and delivery; no real provisioning, natural intake, general worker retrieval or mirror cutover'}))
asyncio.run(main())
