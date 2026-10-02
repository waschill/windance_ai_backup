"""Synthetic Messages schema: exact match, wrong/group/stale/ambiguous/failure cases."""
import hashlib,json,sqlite3,tempfile
from pathlib import Path
from messages_delivery_evidence import observe
results=[]
with tempfile.TemporaryDirectory() as tmp:
    for case in ('delivered','sent_only','wrong_recipient','group','stale','duplicate','incoming','sms','error','null_error','no_delivery_date','attributed_only'):
        p=Path(tmp)/(case+'.db');c=sqlite3.connect(p)
        c.executescript('CREATE TABLE message(text TEXT,service TEXT,is_from_me INTEGER,is_sent INTEGER,is_delivered INTEGER,date_delivered INTEGER,error INTEGER);CREATE TABLE handle(id TEXT);CREATE TABLE chat_message_join(chat_id INTEGER,message_id INTEGER);CREATE TABLE chat_handle_join(chat_id INTEGER,handle_id INTEGER);')
        c.execute('INSERT INTO handle VALUES(?)',('other' if case=='wrong_recipient' else 'synthetic-owner',))
        c.execute('INSERT INTO chat_handle_join VALUES(1,1)')
        if case=='group':c.execute("INSERT INTO handle VALUES('other')");c.execute('INSERT INTO chat_handle_join VALUES(1,2)')
        row=(None if case=='attributed_only' else 'PRIVATE_SENTINEL','SMS' if case=='sms' else 'iMessage',0 if case=='incoming' else 1,1,0 if case=='sent_only' else 1,0 if case=='no_delivery_date' else 100,None if case=='null_error' else 9 if case=='error' else 0)
        c.execute('INSERT INTO message VALUES(?,?,?,?,?,?,?)',row);c.execute('INSERT INTO chat_message_join VALUES(1,1)')
        if case=='duplicate':c.execute('INSERT INTO message VALUES(?,?,?,?,?,?,?)',row);c.execute('INSERT INTO chat_message_join VALUES(1,2)')
        c.commit();c.close();before=hashlib.sha256(p.read_bytes()).hexdigest()
        result=observe(p,'synthetic-owner','PRIVATE_SENTINEL',1 if case=='stale' else 0)
        assert (result['status']=='delivered')==(case=='delivered')
        if case=='duplicate':assert result['status']=='ambiguous'
        assert 'PRIVATE_SENTINEL' not in json.dumps(result) and 'synthetic-owner' not in json.dumps(result)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==before
        results.append({'case':case,'status':result['status']})
    absent=Path(tmp)/'absent.db';assert observe(absent,'owner','body',0)['status']=='unavailable' and not absent.exists()
    assert observe(p,'owner','body',True)['status']=='unavailable'
print(json.dumps({'cases':results,'missing_database_not_created':True,'boolean_boundary_rejected':True,'private_content_excluded':True,'source_databases_unchanged':True,'real_sends':0}))
