"""Actual persistent loop/guardian/runtime CLI, with synthetic transport shim."""
from contextlib import closing
import json,os,shutil,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
from message_receipt_journal import Journal
from keyed_outbox_admission import admit
from keyed_outbox_status import lookup

wheel,source,fixtures=map(lambda x:Path(x).resolve(),sys.argv[1:])
items=json.loads(fixtures.read_text(encoding='utf-8-sig'))
chunks=[next(x['expected'] for x in items if x['name']==n) for n in ('plain','unicode')]
runtime=['receipt_outbox_dispatcher.py','bounded_outbox_request.py','outbox_request_guardian.py',
         'receipt_request_worker.py','test_worker_cli_composition.py','receipt_queue_handler.py',
         'receipt_chunk_coordinator.py','message_receipt_journal.py','messages_store_checkpoint.py',
         'bounded_message_observer.py','messages_attributed_receipt.py','attributed_text_candidate.py','await_message_receipt.py']
results=[]
with tempfile.TemporaryDirectory(prefix='windance-persistent-flow-') as tmp:
    stage=Path(tmp)/'runtime';stage.mkdir()
    for name in runtime:shutil.copyfile(Path(__file__).with_name(name),stage/name)
    (stage/'receipt_request_worker.py').rename(stage/'receipt_request_worker_runtime.py')
    (stage/'receipt_request_worker.py').write_text('''import argparse,importlib.util,json,os,sys
from pathlib import Path
p=argparse.ArgumentParser()
for n in ('root','source','database','wheel','request-id','contract'):p.add_argument('--'+n,required=True)
a=p.parse_args();root=Path(a.root)
(root/'worker-process.json').write_text(json.dumps({'pid':os.getpid(),'pgid':os.getpgrp()}))
spec=importlib.util.spec_from_file_location('receipt_request_worker',Path(__file__).with_name('receipt_request_worker_runtime.py'))
m=importlib.util.module_from_spec(spec);sys.modules['receipt_request_worker']=m;spec.loader.exec_module(m)
from test_worker_cli_composition import child
child(root,'auto_'+(root/'phase').read_text(),Path(a.wheel),Path(a.source),Path('''+repr(str(fixtures))+'''))
''')
    for case in ('delayed','hang_after_send','parent_loss'):
        root=Path(tmp)/case;root.mkdir()
        for folder in ('queue','results','claims'):(root/folder).mkdir()
        Journal(root/'journal.db',create=True)
        with closing(sqlite3.connect(root/'messages.db')) as c:
            c.executescript("CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER,guid TEXT);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);INSERT INTO handle VALUES('synthetic-owner');INSERT INTO chat_handle_join VALUES(1,1);INSERT INTO message(guid,is_from_me) VALUES('seed-guid',0);");c.commit()
        payload={'to':'synthetic-owner','chunks':chunks,'sms':False};key='synthetic'
        assert admit(root,key,payload)['status']=='pending'
        (root/'phase').write_text('hang_after_send' if case=='parent_loss' else case)
        command=[sys.executable,'-B',str(stage/'receipt_outbox_dispatcher.py'),'--root',str(root),
                 '--source',str(source),'--database',str(root/'messages.db'),'--wheel',str(wheel),
                 '--request-seconds','10' if case=='parent_loss' else '1.5']
        def start():return subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def count():
            with closing(sqlite3.connect(root/'messages.db')) as c:return c.execute('SELECT count(*) FROM message WHERE is_from_me=1').fetchone()[0]
        dispatcher=start()
        try:
            if case=='parent_loss':
                deadline=time.monotonic()+3
                while count()!=1:
                    assert dispatcher.poll() is None and time.monotonic()<deadline
                    time.sleep(.03)
                worker=json.loads((root/'worker-process.json').read_text())
                dispatcher.kill();dispatcher.wait(timeout=2)
                deadline=time.monotonic()+2
                while True:
                    state=subprocess.run(['/bin/ps','-o','stat=','-p',str(worker['pid'])],capture_output=True,text=True,timeout=1).stdout.strip()
                    if not state or state.startswith('Z'):break
                    assert time.monotonic()<deadline,'worker survived dispatcher death'
                    time.sleep(.03)
                (root/'phase').write_text('resume');dispatcher=start()
            deadline=time.monotonic()+6
            while list((root/'queue').glob('*.json')):
                assert dispatcher.poll() is None and time.monotonic()<deadline,(case,'queue not settled')
                time.sleep(.05)
            expected='verified_delivery' if case=='delayed' else 'uncertain'
            assert lookup(root,key,payload)['status']==expected
            before=count();assert before==(2 if case=='delayed' else 1)
            time.sleep(.6)
            assert count()==before and dispatcher.poll() is None
            results.append({'case':case,'outcome':expected,'synthetic_sends':before,'duplicate_sends':0})
        finally:
            if dispatcher.poll() is None:dispatcher.terminate()
            dispatcher.wait(timeout=3)
print(json.dumps({'status':'passed','cases':results,'real_sends':0,'test_dispatchers_stopped':True}))
