"""Installed SAL run loop, real loopback HTTP, actual manager schema; synthetic data."""
import ast,asyncio,json,re,sqlite3,subprocess,tempfile,urllib.error
from pathlib import Path
from types import SimpleNamespace
from aiohttp import web
from aiohttp.test_utils import TestServer
from authenticated_message_ingress import Adapter,Intake
from authenticated_messages_adapter import submit

async def main():
    root=Path(__file__).resolve().parent
    sender=json.loads((root/'installed-sender-run-20261002.json').read_text(encoding='utf-8-sig'))
    harness=Path('/Users/herald/services/agent-harness/agent_harness.py').read_text()
    names={'parse_remember_command','memory_looks_secret'}
    functions=[n for n in ast.parse(harness).body if getattr(n,'name','') in names]
    policy={'re':re};exec(compile(ast.Module(body=functions,type_ignores=[]),'<installed-policy>','exec'),policy)
    def validate(text):
        # Expand addressing/scope/correction grammar before the installed classifier.
        from source_memory_api import explicit_intent,explicit_change
        intent=explicit_intent(text,policy['parse_remember_command'])
        change=explicit_change(text)
        value=intent[1] if intent else change[2] if change and change[0]=='correct' else None
        return value is None or not policy['memory_looks_secret'](value)
    class Closing(sqlite3.Connection):
        def __exit__(self,*args):
            try:return super().__exit__(*args)
            finally:self.close()
    class Done(Exception):pass
    with tempfile.TemporaryDirectory(prefix='sender-intake-chain-') as directory:
        base=Path(directory)
        def connect():return sqlite3.connect(base/'manager.db',factory=Closing)
        source=Path('/Users/herald/services/vega-manager/manager.py').read_text()
        node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='init')
        ns={'BASE':base,'connect':connect};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-init>','exec'),ns);ns['init']()
        with connect() as c:Intake.install(c)
        intake=Intake([Adapter('fixture-sal','fixture-adapter',frozenset({'william','shawn'}),'max-imessage',True)],connect,validate)
        app=web.Application();app.router.add_post('/messages/authenticated',intake.handle)
        async with TestServer(app) as server:
            endpoint=str(server.make_url('/messages/authenticated'))
            cursor=[0];attempts=[];outbox={};failed=[False]
            rows=[(1,'fixture first','fixture-william',True),(2,'fixture group','fixture-william',False),
                  (3,'fixture last','fixture-shawn',True)]
            def ask(text,sender,rowid):return submit(endpoint,'fixture-adapter',{'fixture-william':'William','fixture-shawn':'Shawn'}[sender],rowid,text)
            def send(sender,text,rowid):
                attempts.append(rowid)
                outbox.setdefault(rowid,(sender,text))
                # Simulate lost acknowledgment after sender accepted row3.
                if rowid==3 and not failed[0]:failed[0]=True;raise RuntimeError('fixture lost receipt')
            def sleep(seconds):
                if seconds!=10:raise Done()
            globals_={'load_cursor':lambda:cursor[0],'save_cursor':lambda row:cursor.__setitem__(0,row),
                'log':lambda *a,**k:None,'pending':lambda after:[r for r in rows if r[0]>after],
                'normalize_sender':lambda value:value,'ALLOWED':{'fixture-william':'William','fixture-shawn':'Shawn'},
                'ask_herald':ask,'send_imessage':send,'sqlite3':sqlite3,'urllib':SimpleNamespace(error=urllib.error),
                'subprocess':subprocess,'json':json,'time':SimpleNamespace(sleep=sleep)}
            exec(compile(sender['run'],'<installed-sender-run>','exec'),globals_)
            def run():
                try:globals_['run']()
                except Done:pass
            await asyncio.to_thread(run)
            assert cursor[0]==3 and attempts==[1,3,3] and len(outbox)==2
            with connect() as c:
                assert c.execute('SELECT owner,session,notify FROM messages ORDER BY created').fetchall()==[('William','william',1),('Shawn','shawn',1)]
                assert c.execute('SELECT count(*) FROM authenticated_message_sources').fetchone()[0]==2
            for index,text in enumerate(['remember this: password SYNTHETIC','Vega, remember for business: api key SYNTHETIC',
                  'correct memory '+'a'*32+': private key SYNTHETIC'],10):
                rejection=await asyncio.to_thread(submit,endpoint,'fixture-adapter','William',index,text)
                assert 'did not store or queue' in rejection and 'SYNTHETIC' not in rejection
            # Run loop advances past deterministic refusal and still accepts next row.
            rows.extend([(4,'remember this: password SYNTHETIC','fixture-william',True),
                         (5,'fixture after rejection','fixture-william',True)])
            await asyncio.to_thread(run)
            assert cursor[0]==5 and 'did not store or queue' in outbox[4][1]
            with connect() as c:assert c.execute('SELECT count(*) FROM messages').fetchone()[0]==3
            try:submit('http://192.0.2.1/messages/authenticated','fixture','William',1,'fixture')
            except ValueError:pass
            else:raise AssertionError('Unprotected remote HTTP accepted')
    print(json.dumps({'installed_sender_sha256':sender['source_sha256'],'installed_run_loop_real_loopback_http':True,
      'two_owner_sessions_and_followup_policy_preserved':True,'retry_created_two_messages_not_three':True,
      'unverified_chat_skipped':True,'installed_classifier_rejects_before_source_storage':True,
      'deterministic_rejection_does_not_block_next_row':True,
      'unprotected_remote_http_rejected':True,'production_changes':False,'actual_sends':0,'dispatches':0,
      'limits':'Synthetic sender map and outbox; no real TLS/tunnel/credential provisioning or actual delivery proof'}))
asyncio.run(main())
