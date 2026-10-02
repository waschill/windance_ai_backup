from contextlib import closing
import json,sqlite3,sys,tempfile
from pathlib import Path
from bounded_outbox_client import submit_and_wait
from bounded_outbox_status import query
from bounded_outbox_request import run_bounded
from message_receipt_journal import Journal

wheel,source,fixtures=map(Path,sys.argv[1:])
items=json.loads(fixtures.read_text(encoding='utf-8-sig'))
chunks=[next(x['expected'] for x in items if x['name']==name) for name in ('plain','unicode')]
results=[]
with tempfile.TemporaryDirectory(prefix='windance-admission-flow-') as tmp:
    for phase in ('delayed','hang_after_send'):
        root=Path(tmp)/phase;root.mkdir()
        for folder in ('claims','queue','results'):(root/folder).mkdir()
        Journal(root/'journal.db',create=True)
        payload={'to':'synthetic-owner','chunks':chunks,'sms':False};key='synthetic-request'
        with closing(sqlite3.connect(root/'messages.db')) as c:
            c.executescript("CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER,guid TEXT);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);INSERT INTO handle VALUES('synthetic-owner');INSERT INTO chat_handle_join VALUES(1,1);INSERT INTO message(guid,is_from_me) VALUES('seed-guid',0);");c.commit()
        first=submit_and_wait(root,key,payload,seconds=.2)
        assert first['reason']=='status_wait_expired',first
        assert len(list((root/'queue').glob('*.json')))==1
        prefix=[sys.executable,'-B',str(Path(__file__).with_name('test_worker_cli_composition.py')),'--child',str(root)]
        tail=list(map(str,(wheel,source,fixtures)))
        result=run_bounded(prefix+['auto_'+phase]+tail,seconds=1.5)
        if phase=='delayed':assert result=={'status':'process_exited','returncode':0},result
        else:assert result['reason']=='whole_request_deadline',result
        for _ in range(2):assert run_bounded(prefix+['auto_resume']+tail,seconds=3)=={'status':'process_exited','returncode':0}
        expected='verified_delivery' if phase=='delayed' else 'uncertain'
        assert query(root,key,payload,seconds=1)['status']==expected
        assert submit_and_wait(root,key,payload,seconds=1)['status']==expected
        assert not list((root/'queue').glob('*.json'))
        with closing(sqlite3.connect(root/'messages.db')) as c:count=c.execute('SELECT count(*) FROM message WHERE is_from_me=1').fetchone()[0]
        assert count==(2 if phase=='delayed' else 1)
        results.append({'case':phase,'final_status':expected,'synthetic_sends':count,'duplicate_sends':0})
print(json.dumps({'status':'passed','cases':results,'real_sends':0}))
