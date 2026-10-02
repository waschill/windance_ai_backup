"""Actual manager schema + HTTP intake + source-bound facts; disposable only."""
import ast
import asyncio
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from authenticated_message_ingress import Adapter, Intake, authenticated_source_loader
from memory_ingress_policy import Policy, Resolver
import owned_fact_store as store
from source_bound_facts import install, record_statement, read_verified


async def main():
    live = Path('/Users/herald/services/vega-manager/manager.py')
    source = live.read_text()
    # Use installed init/schema with disposable BASE and connection only.
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', '') == 'init')
    class Closing(sqlite3.Connection):
        def __exit__(self, *args):
            try: return super().__exit__(*args)
            finally: self.close()
    with tempfile.TemporaryDirectory(prefix='authenticated-intake-') as directory:
        base = Path(directory)
        def connect():
            c = sqlite3.connect(base/'manager.db', factory=Closing)
            c.execute('PRAGMA foreign_keys=ON')
            return c
        scope = {'BASE': base, 'connect': connect}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-manager-init>', 'exec'), scope)
        scope['init']()
        with connect() as c: Intake.install(c)
        intake = Intake([Adapter('fixture-sal', 'fixture-intake', frozenset({'william'}), 'imessage')], connect,
                        lambda text: 'SYNTHETIC_REJECTED' not in text)
        app = web.Application(); app.router.add_post('/messages/authenticated', intake.handle)
        async with TestClient(TestServer(app)) as client:
            body = {'owner': 'william', 'source_id': 'fixture-row-1', 'message': 'remember this: synthetic preference'}
            async def post(payload=body, credential='fixture-intake'):
                return await client.post('/messages/authenticated', json=payload, headers={'Authorization': 'Bearer '+credential})
            assert (await post(credential='wrong')).status == 403
            assert (await post({**body, 'owner': 'shawn'})).status == 403
            assert (await post({**body, 'session': 'shawn'})).status == 422
            assert (await post({**body, 'notify': True})).status == 422
            rejected = await post({**body, 'message':'remember this: SYNTHETIC_REJECTED'})
            assert rejected.status == 422 and 'SYNTHETIC_REJECTED' not in await rejected.text()
            first = await post(); assert first.status == 202
            receipt = await first.json(); mid = receipt['id']
            assert (await (await post()).json())['replayed'] is True
            assert (await post({**body, 'message': 'changed source'})).status == 409
            with connect() as c:
                assert c.execute('SELECT count(*) FROM messages').fetchone()[0] == 1
                assert c.execute('SELECT owner,channel,session,notify FROM messages').fetchone() == ('William','imessage','william',0)
            loader = authenticated_source_loader(connect)
            assert loader('william', receipt['source_ref']).text == body['message']
            try: loader('shawn', receipt['source_ref'])
            except PermissionError: pass
            else: raise AssertionError('Cross-owner source accepted')
            with connect() as c:
                c.execute("INSERT INTO messages(id,request,owner,channel) VALUES('legacy','remember this: synthetic legacy','William','imessage')")
            try: loader('william', 'manager-message:legacy')
            except KeyError: pass
            else: raise AssertionError('Unattested legacy source accepted')
            resolver = Resolver([Policy('fixture-memory', 'fixture-memory-token', frozenset({('william','imessage','personal','write')}))])
            with sqlite3.connect(base/'facts.db') as c:
                store.install(c); install(c)
                result = record_statement(resolver,c,'Bearer fixture-memory-token',loader,lambda value:True,
                  event_id='fixture-event',owner='william',channel='imessage',scope='personal',kind='source_quote',key='preference',
                  source_ref=receipt['source_ref'],quote='synthetic preference')
                assert result['revision'] == 1
                assert read_verified(c,'william','william','personal','source_quote','preference',loader)['value'] == 'synthetic preference'
            # A failed attestation insert rolls back its message as well.
            with connect() as c:
                c.execute("CREATE TRIGGER reject_fixture BEFORE INSERT ON authenticated_message_sources BEGIN SELECT RAISE(ABORT,'fixture'); END")
            failure = await post({**body,'source_id':'fixture-row-failed'})
            assert failure.status == 503 and 'fixture' not in await failure.text()
            with connect() as c:
                assert c.execute('SELECT count(*) FROM messages').fetchone()[0] == 2
                c.execute('DROP TRIGGER reject_fixture')
                c.execute('UPDATE messages SET request=? WHERE id=?', ('modified source',mid))
            try: loader('william',receipt['source_ref'])
            except KeyError: pass
            else: raise AssertionError('Changed source accepted')
    print(json.dumps({'actual_manager_source_sha256':hashlib.sha256(live.read_bytes()).hexdigest(),
      'actual_manager_schema':True,'http_adapter_authentication':True,'owner_session_delivery_fields_bound':True,
      'idempotent_retry_and_conflict':True,'source_and_message_atomic':True,'legacy_and_changed_sources_rejected':True,
      'source_bound_memory_chain':True,'production_changes':False,'dispatches':0,'model_calls':0,
      'limits':'Synthetic adapter; actual SAL transport/provisioning and production route integration pending'}))

asyncio.run(main())
