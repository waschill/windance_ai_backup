"""Actual daemon main/owner lock plus staged queue and real observer, fake transport."""
import base64
from contextlib import closing
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import shutil
import threading
import time


def setup_modules(wheel,source):
    assert hashlib.sha256(wheel.read_bytes()).hexdigest()=='499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'
    sys.path.insert(0,str(wheel.resolve()))
    spec=importlib.util.spec_from_file_location('actual_outbox',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def child(root,phase,wheel,source,fixtures):
    daemon=setup_modules(wheel,source)
    from message_receipt_journal import Journal
    from messages_attributed_receipt import observe
    from bounded_message_observer import observe_bounded
    from messages_store_checkpoint import checkpoint
    from await_message_receipt import await_receipt
    from receipt_chunk_coordinator import run_request
    data=json.loads(fixtures.read_text(encoding='utf-8-sig'))
    selected=[next(c for c in data if c['name']==name) for name in ('plain','unicode')]
    bodies=[c['expected'] for c in selected]
    blobs={c['expected']:base64.b64decode(c['base64']) for c in selected}
    database=root/'messages.db'
    def capture():
        return checkpoint(database)
    def fake_subprocess(command,**kwargs):
        assert command[0]=='/usr/bin/osascript' and command[-3]=='synthetic-owner' and command[-1]=='false'
        body=command[-2]
        assert body in blobs
        with closing(sqlite3.connect(database)) as c:
            cursor=c.execute('INSERT INTO message VALUES(NULL,?,\'iMessage\',1,1,?,100,0,?)',(blobs[body],0 if phase in ('sent_only','delayed') else 1,'guid-'+str(len(body))))
            c.execute('INSERT INTO chat_message_join VALUES(1,?)',(cursor.lastrowid,));c.commit()
        if phase=='delayed':
            def deliver():
                with closing(sqlite3.connect(database)) as c:
                    c.execute('UPDATE message SET is_delivered=1 WHERE is_from_me=1');c.commit()
            threading.Timer(0.2,deliver).start()
        if phase=='replace_store':
            replacement=root/'replacement.db';shutil.copyfile(database,replacement);os.replace(replacement,database)
        if phase=='change_anchor':
            with closing(sqlite3.connect(database)) as c:
                c.execute("UPDATE message SET guid='changed' WHERE ROWID=1");c.commit()
        if phase=='after_send':os._exit(73)
        if phase=='hang_after_send':time.sleep(60)
        return subprocess.CompletedProcess(command,0,'','')
    # Substitute a module-local subprocess object so observer supervision retains
    # its real subprocess implementation. No mutation to global subprocess.run.
    from types import SimpleNamespace
    daemon.subprocess=SimpleNamespace(run=fake_subprocess)
    def deny(event,args):
        if event=='subprocess.Popen':
            command=args[1]
            allowed=(command[0]==sys.executable and len(command)==5 and command[2]==str(Path(__file__).with_name('bounded_message_observer.py').resolve()) and command[3]=='--worker') or (command[0]=='/bin/ps' and command[1:3]==['-o','rss='])
            if not allowed:raise AssertionError('unexpected_child')
        elif event in ('os.system','os.posix_spawn') or event.startswith('socket.'):
            raise AssertionError('external_effect_attempted')
    sys.addaudithook(deny)
    def execute(j,request_id,recipient,chunks):
        def observed(recipient,text,boundary,snapshot,remaining):
            result=observe_bounded(database,recipient,text,boundary,wheel,snapshot,budget_seconds=remaining)
            (root/'observer-diagnostic.json').write_text(json.dumps(result))
            return result
        original_begin=j.begin
        def begin(*args):
            value=original_begin(*args)
            if phase=='after_attempt' and value=='attempt_committed':os._exit(73)
            if phase=='hang_after_attempt' and value=='attempt_committed':time.sleep(60)
            return value
        j.begin=begin
        original_confirm=j.confirm
        def confirm(*args):
            value=original_confirm(*args)
            if phase=='after_receipt' and value=='receipt_committed':os._exit(73)
            return value
        j.confirm=confirm
        return actual_execute_request(j,request_id,recipient,chunks,daemon,database,wheel,receipt_seconds=0.7)
    from receipt_queue_handler import handle
    daemon.ROOT=root;daemon.QUEUE=root/'queue';daemon.RESULTS=root/'results';daemon.LOG=root/'daemon.log'
    daemon.handle=lambda path:handle(daemon,path,root/'journal.db',execute)
    atomic=daemon.atomic_json
    def atomic_hook(path,value):
        atomic(path,value)
        if phase=='after_result' and path.parent.name=='results':os._exit(73)
    daemon.atomic_json=atomic_hook
    import receipt_request_worker as worker
    actual_execute_request=worker.execute_request
    worker.execute_request=lambda j,r,to,chunks,host,db,wh,**kw:execute(j,r,to,chunks)
    original_spec=worker.importlib.util.spec_from_file_location
    def instrumented_spec(name,path,*args,**kwargs):
        spec=original_spec(name,path,*args,**kwargs)
        if name=='pinned_outbox_host':
            original_exec=spec.loader.exec_module
            def load(module):
                original_exec(module)
                module.subprocess=SimpleNamespace(run=fake_subprocess)
                module.atomic_json=atomic_hook
            spec.loader.exec_module=load
        return spec
    worker.importlib.util.spec_from_file_location=instrumented_spec
    sys.argv=['receipt_request_worker.py','--source',str(source),'--root',str(root),
              '--database',str(database),'--wheel',str(wheel),'--request-id','request']
    worker.main()
    if not list((root/'results').glob('*.json')):
        print(json.dumps({'status':'lock_held'}));return
    result_paths=list((root/'results').glob('*.json'))
    assert len(result_paths)==1
    print(result_paths[0].read_text())


def parent(wheel,source,fixtures):
    from message_receipt_journal import Journal
    results=[]
    with tempfile.TemporaryDirectory(prefix='windance-receipt-composition-') as tmp:
        for phase in ('normal','sent_only','after_attempt','after_send','after_receipt','replace_store','change_anchor','delayed','after_result'):
            root=Path(tmp)/phase;root.mkdir()
            Journal(root/'journal.db',create=True)
            (root/'queue').mkdir();(root/'results').mkdir()
            fixture_data=json.loads(fixtures.read_text(encoding='utf-8-sig'))
            chunks=[next(item['expected'] for item in fixture_data if item['name']==name) for name in ('plain','unicode')]
            (root/'queue/request.json').write_text(json.dumps({'to':'synthetic-owner','chunks':chunks,'sms':False}))
            with closing(sqlite3.connect(root/'messages.db')) as c:
                c.executescript('CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER,guid TEXT);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);INSERT INTO handle VALUES(\'synthetic-owner\');INSERT INTO chat_handle_join VALUES(1,1);INSERT INTO message(guid,is_from_me) VALUES(\'seed-guid\',0);');c.commit()
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(root)]
            tail=[str(wheel),str(source),str(fixtures)]
            if phase=='normal':
                import fcntl
                with (root/'owner.lock').open('a') as owner:
                    fcntl.flock(owner.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                    contender=subprocess.run(command+['normal']+tail,capture_output=True,timeout=10)
                    assert contender.returncode==0 and json.loads(contender.stdout)['status']=='lock_held'
                    assert (root/'queue/request.json').exists()
            first=subprocess.run(command+[phase]+tail,capture_output=True,timeout=10)
            assert first.returncode==(73 if phase.startswith('after_') else 0),(phase,first.returncode)
            def count():
                with closing(sqlite3.connect(root/'messages.db')) as c:return c.execute('SELECT count(*) FROM message WHERE is_from_me=1').fetchone()[0]
            before=count()
            second=subprocess.run(command+['resume']+tail,capture_output=True,timeout=10)
            assert second.returncode==0,(phase,'resume failed')
            result=json.loads(second.stdout)
            after=count()
            third=subprocess.run(command+['resume']+tail,capture_output=True,timeout=10)
            assert third.returncode==0 and count()==after,(phase,'later restart replayed')
            # Completed first chunk is safe to continue only when no attempt is unresolved.
            if phase=='after_receipt':
                assert (before,after)==(1,2) and result['status']=='delivered'
            else:
                assert after==before,(phase,'replayed')
                assert (result['status']=='delivered')==(phase in ('normal','delayed','after_result'))
            assert len(set([row[0] for row in sqlite_rows(root/'messages.db')]))==after
            assert not (root/'queue/request.json').exists()
            if result['status']=='delivered':assert not (root/'inflight/request.json').exists()
            else:assert (root/'uncertain/request.json').exists()
            results.append({'phase':phase,'messages_before_restart':before,'messages_after_restart':after,'status':result['status']})
    print(json.dumps({'status':'passed','cases':results,'real_sends':0,'production_changed':False}))


def sqlite_rows(path):
    with closing(sqlite3.connect(path)) as c:return c.execute('SELECT attributedBody FROM message WHERE is_from_me=1').fetchall()


if __name__=='__main__':
    if sys.argv[1]=='--child':child(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]),Path(sys.argv[5]),Path(sys.argv[6]))
    else:parent(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))

