"""Synthetic actual SQLite schema and real pinned archive decoder composition."""
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

wheel=Path(sys.argv[1])
assert hashlib.sha256(wheel.read_bytes()).hexdigest()=='499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278'
sys.path.insert(0,str(wheel.resolve()))
from messages_attributed_receipt import observe
fixtures={x['name']:x for x in json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))}
blob=lambda name:base64.b64decode(fixtures[name]['base64'])
target=fixtures['plain']['expected']
cases=['plain','attributed','unicode','both_agree','both_conflict','sent_only','wrong_recipient',
       'group','stale','duplicate','incoming','sms','error','null_error','no_delivery_date',
       'malformed','wrong_root','embedded','metadata','unknown_plus_match','oversized',
       'limit_exceeded','multiple_chat_joins','missing_content','unrelated_plus_match']
results=[]
with tempfile.TemporaryDirectory() as tmp:
    for case in cases:
        p=Path(tmp)/(case+'.db')
        c=sqlite3.connect(p)
        c.executescript('CREATE TABLE message(text TEXT,attributedBody BLOB,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);')
        c.execute('INSERT INTO handle VALUES(?)',('other' if case=='wrong_recipient' else 'synthetic-owner',))
        c.execute('INSERT INTO chat_handle_join VALUES(1,1)')
        if case=='group':
            c.execute("INSERT INTO handle VALUES('other')")
            c.execute('INSERT INTO chat_handle_join VALUES(1,2)')
        archive=blob('unicode' if case=='unicode' else 'wrong_root' if case=='wrong_root' else case if case in ('embedded','metadata') else 'plain')
        plain=target if case in ('plain','both_agree') else 'conflicting body' if case=='both_conflict' else None
        if case in ('plain','missing_content'):archive=None
        if case=='malformed':archive=b'broken archive'
        if case=='oversized':archive=b'x'*262145
        row=(plain,archive,'SMS' if case=='sms' else 'iMessage',0 if case=='incoming' else 1,1,
             0 if case=='sent_only' else 1,0 if case=='no_delivery_date' else 100,
             None if case=='null_error' else 9 if case=='error' else 0)
        def add(values):
            cursor=c.execute('INSERT INTO message VALUES(?,?,?,?,?,?,?,?)',values)
            c.execute('INSERT INTO chat_message_join VALUES(1,?)',(cursor.lastrowid,))
        add(row)
        if case=='duplicate':add(row)
        if case in ('unknown_plus_match','unrelated_plus_match'):
            add((None,b'broken' if case=='unknown_plus_match' else blob('embedded'),'iMessage',1,1,1,100,0))
        if case=='limit_exceeded':
            for _ in range(100):add((None,blob('embedded'),'iMessage',1,1,1,100,0))
        if case=='multiple_chat_joins':c.execute('INSERT INTO chat_message_join VALUES(2,1)')
        c.commit();c.close()
        before=hashlib.sha256(p.read_bytes()).hexdigest()
        expected=fixtures['unicode']['expected'] if case=='unicode' else 'EXPECTED' if case in ('embedded','metadata') else target
        result=observe(p,'synthetic-owner',expected,1 if case=='stale' else 0)
        assert (result['status']=='delivered')==(case in ('plain','attributed','unicode','both_agree','unrelated_plus_match')),case
        if case=='duplicate':assert result['status']=='ambiguous'
        if case=='unknown_plus_match':assert result['reason']=='candidate_content_unverifiable'
        if case=='limit_exceeded':assert result['reason']=='candidate_limit_exceeded'
        assert expected not in json.dumps(result) and 'synthetic-owner' not in json.dumps(result)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==before
        results.append({'case':case,'status':result['status']})
    missing=Path(tmp)/'absent.db'
    assert observe(missing,'owner','body',0)['status']=='unavailable' and not missing.exists()
    for bad in (True,-1,2**63,'0',None):
        assert observe(p,'owner','body',bad)['reason']=='invalid_correlation_input'
print(json.dumps({'status':'passed','cases':results,'database_hashes_unchanged':True,'sends':0,'private_content_excluded':True}))
