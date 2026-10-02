"""SAL private candidate AST functions, disposable data, intercepted HTTP/sender."""
import ast
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import urllib.request
import urllib.error

root=Path('/Users/zuzu/backups/sender-boundary-candidate-20261002')
sys.path.insert(0,str(root))
from bridge_sender_boundary import normalize_sender,pending_messages
source=(root/'imessage_herald_bridge.py').read_text()
names={'normalize_sender','pending','load_cursor','save_cursor','ask_herald','send_imessage','run'}
nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(nodes)==len(names)
class Done(Exception):pass
results=[]
for failure in ['none','sender','http']:
    with tempfile.TemporaryDirectory(prefix='windance-bridge-fixture-') as directory:
        d=Path(directory); database=d/'messages.db';state=d/'cursor';state.write_text('0\n')
        with sqlite3.connect(database) as c:
            c.executescript('''CREATE TABLE message(ROWID INTEGER PRIMARY KEY,text TEXT,handle_id INTEGER,is_from_me INTEGER);
            CREATE TABLE handle(ROWID INTEGER PRIMARY KEY,id TEXT);
            CREATE TABLE chat(ROWID INTEGER PRIMARY KEY,style INTEGER,room_name TEXT);
            CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);
            CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);
            INSERT INTO handle VALUES(1,'+1 202 555 0101'),(2,'+1 202 555 0102'),(3,'12025550101@example.test');
            INSERT INTO message VALUES(1,'fixture-one',1,0),(2,'fixture-group',1,0),(3,'fixture-collision',3,0),(4,'fixture-four',2,0);
            INSERT INTO chat VALUES(1,45,''),(2,43,'fixture-room'),(3,45,''),(4,45,'');
            INSERT INTO chat_message_join VALUES(1,1),(2,2),(3,3),(4,4);
            INSERT INTO chat_handle_join VALUES(1,1),(2,1),(2,2),(3,3),(4,2);''')
        posts=[];sends=[];logs=[];failed=[False];retry_cursors=[]
        def urlopen(request,timeout):
            payload=json.loads(request.data);posts.append(payload)
            if failure=='http' and payload['request_id']=='max-imessage:4' and not failed[0]:
                failed[0]=True;raise urllib.error.URLError('fixture network interruption')
            return io.BytesIO(b'{"reply":"fixture answer","agent":"Vega"}')
        def send(command,check,timeout):
            assert command[0]=='/usr/bin/python3' and command[1]=='fixture-sender'
            payload=json.loads(base64.b64decode(command[2]));sends.append(payload)
            if failure=='sender' and payload['idempotency_key']=='max-inbound-ack:4' and not failed[0]:
                failed[0]=True;raise subprocess.CalledProcessError(1,['fixture-sender'])
            return SimpleNamespace(returncode=0)
        def sleep(seconds):
            if seconds==10:
                retry_cursors.append(int(state.read_text()));return
            raise Done()
        namespace={'sqlite3':sqlite3,'DB':database,'STATE':state,'os':os,'json':json,'base64':base64,
          'ALLOWED':{'12025550101':'William','12025550102':'Shawn'},'HERALD':'http://fixture.invalid/message','SENDER':'fixture-sender',
          'urllib':SimpleNamespace(request=SimpleNamespace(Request=urllib.request.Request,urlopen=urlopen),error=urllib.error),
          'subprocess':SimpleNamespace(run=send,SubprocessError=subprocess.SubprocessError),
          'time':SimpleNamespace(sleep=sleep),'log':lambda event,**fields:logs.append((event,fields)),
          'strict_normalize_sender':normalize_sender,'pending_messages':pending_messages}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<candidate-functions>','exec'),namespace)
        try:namespace['run']()
        except Done:pass
        expected=['max-imessage:1','max-imessage:4']+(['max-imessage:4'] if failure!='none' else [])
        assert [p['request_id'] for p in posts]==expected
        assert all(p['user']==('William' if p['request_id'].endswith(':1') else 'Shawn') for p in posts)
        assert int(state.read_text())==4
        assert [x for x in logs if x[0].startswith('message_skipped')]==[
            ('message_skipped_unverified_chat',{'rowid':2}),('message_skipped_unapproved',{'rowid':3})]
        assert retry_cursors==([] if failure=='none' else [3])
        assert all(s['idempotency_key'] in {'max-inbound-ack:1','max-inbound-ack:4'} for s in sends)
        assert len(sends)==(3 if failure=='sender' else 2)
        results.append({'scenario':failure,'request_ids':[p['request_id'] for p in posts],
          'sender_envelope_attempts':len(sends),'cursor_after':4,'retry_cursors':retry_cursors,'passed':True})
print(json.dumps({'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'scenarios':results,
 'real_http_calls':0,'real_sends':0,'production_cursor_writes':0,
 'limits':'Stable keys preserved. Sender deduplication and manager persistence were mocked, not proven.'},indent=2))
