"""Actual producer main killed while waiting, followed by full staged queue/status."""
import base64
from contextlib import closing
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from keyed_outbox_status import lookup
from message_receipt_journal import Journal


def producer_at(source,root):
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f'
    spec=importlib.util.spec_from_file_location('producer',source)
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    p.ROOT=root;p.QUEUE=root/'queue';p.RESULTS=root/'results'
    return p


def client(source,root):
    p=producer_at(source,root)
    body=(root/'synthetic-input.json').read_bytes()
    sys.argv=['synthetic-client',base64.b64encode(body).decode()]
    sys.exit(p.main())


def parent(wheel,daemon,producer,fixtures):
    items=json.loads(fixtures.read_text(encoding='utf-8-sig'))
    chunks=[next(item['expected'] for item in items if item['name']==name) for name in ('plain','unicode')]
    rows=[]
    with tempfile.TemporaryDirectory(prefix='windance-lost-reply-') as tmp:
        for phase in ('delayed','after_send'):
            root=Path(tmp)/phase;root.mkdir()
            Journal(root/'journal.db',create=True)
            payload={'to':'synthetic-owner','chunks':chunks,'sms':False};key='synthetic-request-key'
            (root/'synthetic-input.json').write_text(json.dumps(dict(payload,idempotency_key=key)))
            with closing(sqlite3.connect(root/'messages.db')) as c:
                c.executescript('CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER,guid TEXT);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);INSERT INTO handle VALUES(\'synthetic-owner\');INSERT INTO chat_handle_join VALUES(1,1);INSERT INTO message(guid,is_from_me) VALUES(\'seed-guid\',0);');c.commit()
            pending=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--client',str(producer),str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                deadline=time.monotonic()+3
                while lookup(root,key,payload)['status']!='pending':
                    assert pending.poll() is None and time.monotonic()<deadline
                    time.sleep(0.02)
                # The actual producer main is alive waiting for its result.
                assert pending.poll() is None
            finally:
                if pending.poll() is None:pending.kill()
                pending.wait(timeout=2)
            assert lookup(root,key,payload)['status']=='pending'
            command=[sys.executable,'-B',str(Path(__file__).with_name('test_full_receipt_queue.py').resolve()),'--child',str(root)]
            tail=[str(wheel),str(daemon),str(fixtures)]
            first=subprocess.run(command+[phase]+tail,capture_output=True,timeout=10)
            assert first.returncode==(73 if phase=='after_send' else 0)
            if phase=='after_send':
                assert lookup(root,key,payload)['status']=='uncertain'
                resumed=subprocess.run(command+['resume']+tail,capture_output=True,timeout=10)
                assert resumed.returncode==0
            status=lookup(root,key,payload)
            assert status['status']==('verified_delivery' if phase=='delayed' else 'uncertain'),status
            def count():
                with closing(sqlite3.connect(root/'messages.db')) as c:return c.execute('SELECT count(*) FROM message WHERE is_from_me=1').fetchone()[0]
            before=count()
            p=producer_at(producer,root)
            result,retained=p.enqueue(payload,key)
            assert retained and result.exists() and not list((root/'queue').glob('*.json'))
            for _ in range(2):
                assert lookup(root,key,payload)==status
            assert count()==before==(2 if phase=='delayed' else 1)
            rows.append({'case':phase,'caller_terminated_while_waiting':True,'final_status':status['status'],'synthetic_sends':before,'repeated_sends':0})
    print(json.dumps({'status':'passed','cases':rows,'real_sends':0,'production_changes':False}))


if __name__=='__main__':
    if sys.argv[1]=='--client':client(Path(sys.argv[2]),Path(sys.argv[3]))
    else:parent(*map(Path,sys.argv[1:]))
