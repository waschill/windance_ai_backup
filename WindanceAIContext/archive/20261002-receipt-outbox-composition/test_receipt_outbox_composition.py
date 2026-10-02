"""Actual outbox send function with subprocess boundary intercepted, real observer/journal."""
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
    from receipt_chunk_coordinator import run_request
    data=json.loads(fixtures.read_text(encoding='utf-8-sig'))
    selected=[next(c for c in data if c['name']==name) for name in ('plain','unicode')]
    bodies=[c['expected'] for c in selected]
    blobs={c['expected']:base64.b64decode(c['base64']) for c in selected}
    database=root/'messages.db'
    def capture():
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as c:
            boundary=c.execute('SELECT COALESCE(MAX(ROWID),0) FROM message').fetchone()[0]
        return {'store_id':'synthetic-store','boundary':boundary}
    def fake_subprocess(command,**kwargs):
        assert command[0]=='/usr/bin/osascript' and command[-3]=='synthetic-owner' and command[-1]=='false'
        body=command[-2]
        assert body in blobs
        with closing(sqlite3.connect(database)) as c:
            cursor=c.execute('INSERT INTO message VALUES(NULL,?,\'iMessage\',1,1,?,100,0)',(blobs[body],0 if phase=='sent_only' else 1))
            c.execute('INSERT INTO chat_message_join VALUES(1,?)',(cursor.lastrowid,));c.commit()
        if phase=='after_send':os._exit(73)
        return subprocess.CompletedProcess(command,0,'','')
    # Keep the exact production send_one body. Intercept its only external effect.
    daemon.subprocess.run=fake_subprocess
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.posix_spawn') or event.startswith('socket.'):
            raise AssertionError('external_effect_attempted')
    sys.addaudithook(deny)
    j=Journal(root/'journal.db')
    original_begin=j.begin
    def begin(*args):
        value=original_begin(*args)
        if phase=='after_attempt' and value=='attempt_committed':os._exit(73)
        return value
    j.begin=begin
    original_confirm=j.confirm
    def confirm(*args):
        value=original_confirm(*args)
        if phase=='after_receipt' and value=='receipt_committed':os._exit(73)
        return value
    j.confirm=confirm
    result=run_request(j,'synthetic-request','synthetic-owner',bodies,capture,
                       lambda recipient,text,boundary:observe(database,recipient,text,boundary),daemon.send_one)
    print(json.dumps(result))


def parent(wheel,source,fixtures):
    from message_receipt_journal import Journal
    results=[]
    with tempfile.TemporaryDirectory(prefix='windance-receipt-composition-') as tmp:
        for phase in ('normal','sent_only','after_attempt','after_send','after_receipt'):
            root=Path(tmp)/phase;root.mkdir()
            Journal(root/'journal.db',create=True)
            with closing(sqlite3.connect(root/'messages.db')) as c:
                c.executescript('CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);INSERT INTO handle VALUES(\'synthetic-owner\');INSERT INTO chat_handle_join VALUES(1,1);');c.commit()
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(root)]
            tail=[str(wheel),str(source),str(fixtures)]
            first=subprocess.run(command+[phase]+tail,capture_output=True,timeout=10)
            assert first.returncode==(73 if phase.startswith('after_') else 0),(phase,first.returncode)
            def count():
                with closing(sqlite3.connect(root/'messages.db')) as c:return c.execute('SELECT count(*) FROM message').fetchone()[0]
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
                assert (result['status']=='delivered')==(phase=='normal')
            assert len(set([row[0] for row in sqlite_rows(root/'messages.db')]))==after
            results.append({'phase':phase,'messages_before_restart':before,'messages_after_restart':after,'status':result['status']})
    print(json.dumps({'status':'passed','cases':results,'real_sends':0,'production_changed':False}))


def sqlite_rows(path):
    with closing(sqlite3.connect(path)) as c:return c.execute('SELECT attributedBody FROM message').fetchall()


if __name__=='__main__':
    if sys.argv[1]=='--child':child(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]),Path(sys.argv[5]),Path(sys.argv[6]))
    else:parent(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
