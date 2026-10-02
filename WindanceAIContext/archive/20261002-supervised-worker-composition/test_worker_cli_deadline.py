"""Full staged queue timeout and restart against synthetic data on SAL."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from bounded_outbox_request import run_bounded
from message_receipt_journal import Journal

wheel,source,fixtures=map(Path,sys.argv[1:])
items=json.loads(fixtures.read_text(encoding='utf-8-sig'))
chunks=[next(item['expected'] for item in items if item['name']==name) for name in ('plain','unicode')]
results=[]
with tempfile.TemporaryDirectory(prefix='windance-request-deadline-') as tmp:
    for phase in ('normal','hang_after_attempt','hang_after_send'):
        root=Path(tmp)/phase;root.mkdir()
        Journal(root/'journal.db',create=True)
        (root/'queue').mkdir();(root/'results').mkdir()
        (root/'queue/request.json').write_text(json.dumps({'to':'synthetic-owner','chunks':chunks,'sms':False}))
        with closing(sqlite3.connect(root/'messages.db')) as c:
            c.executescript('CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER,guid TEXT);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);INSERT INTO handle VALUES(\'synthetic-owner\');INSERT INTO chat_handle_join VALUES(1,1);INSERT INTO message(guid,is_from_me) VALUES(\'seed-guid\',0);');c.commit()
        prefix=[sys.executable,'-B',str(Path(__file__).with_name('test_worker_cli_composition.py')),'--child',str(root)]
        tail=[str(wheel),str(source),str(fixtures)]
        start=time.monotonic()
        result=run_bounded(prefix+[phase]+tail,seconds=1.5)
        elapsed=time.monotonic()-start
        def count():
            with closing(sqlite3.connect(root/'messages.db')) as c:return c.execute('SELECT COUNT(*) FROM message WHERE is_from_me=1').fetchone()[0]
        before=count()
        if phase=='normal':assert result=={'status':'process_exited','returncode':0}
        else:
            assert result=={'status':'uncertain','reason':'whole_request_deadline'}
            assert 1.4<=elapsed<2
            assert Journal(root/'journal.db').status('request')['chunks'][0]=='attempting'
        import fcntl
        with (root/'owner.lock').open('a') as owner:
            fcntl.flock(owner.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        for _ in range(2):
            resumed=run_bounded(prefix+['resume']+tail,seconds=3)
            assert resumed=={'status':'process_exited','returncode':0}
        assert count()==before
        final=json.loads((root/'results/request.json').read_text())
        assert (final['status']=='delivered')==(phase=='normal'),(phase,final,Journal(root/'journal.db').status('request'),(root/'observer-diagnostic.json').read_text() if (root/'observer-diagnostic.json').exists() else 'none')
        if phase!='normal':assert (root/'uncertain/request.json').exists()
        results.append({'phase':phase,'seconds':round(elapsed,3),'synthetic_sends':before,'status':final['status'],'repeated_sends':0})
print(json.dumps({'status':'passed','cases':results,'real_sends':0,'production_changed':False}))
