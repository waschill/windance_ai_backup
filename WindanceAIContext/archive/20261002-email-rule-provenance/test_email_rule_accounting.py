import json,sqlite3,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1]).resolve()))
from email_action_intent import SCHEMA,perform,OutcomeHeld
from email_rule_accounting import evidence,reconcile,expected
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'state.db'
    def connect():return sqlite3.connect(path)
    c=connect();c.executescript(SCHEMA+'''
CREATE TABLE email_sender_rule_receipts(operation_key TEXT PRIMARY KEY,sender_key TEXT,rule_action TEXT,recorded_at TEXT);
CREATE TABLE max_email_sender_rules(sender_email TEXT PRIMARY KEY,action TEXT,last_matched_at TEXT,match_count INTEGER DEFAULT 0);
CREATE TABLE max_email_tracking(message_id TEXT PRIMARY KEY,thread_id TEXT,sender TEXT,subject TEXT,first_seen_at TEXT,last_seen_at TEXT,last_gmail_state TEXT,max_state TEXT,importance TEXT,follow_up_state TEXT,notes TEXT);
INSERT INTO max_email_sender_rules(sender_email,action) VALUES('fixture@example.invalid','always_delete');
''');c.close()
    calls=[]
    def make(i):return evidence('fixture@example.invalid','always_delete',{'id':f'fixture-{i}','from':'fixture@example.invalid','subject':'Synthetic','body':'PRIVATE_BODY_NOT_STORED'},'normal','unread')
    def run(i):
        item=make(i);key,digest=expected(item)
        def effect():
            c=connect();row=c.execute('SELECT evidence_json,applied FROM email_rule_provenance WHERE operation_key=?',(key,)).fetchone();c.close()
            assert row and row[1]==0 and 'PRIVATE_BODY_NOT_STORED' not in row[0]
            calls.append(i);return {'trashed':True,'id':item['id']}
        return perform(connect,'william',item['id'],'trash',{'sender_rule':item['rule_key'],'rule_action':item['rule_action']},effect,rule_evidence=item)
    for i in range(25):run(i)
    assert reconcile(connect)==20 and reconcile(connect)==5 and reconcile(connect)==0
    c=connect();assert c.execute('SELECT match_count FROM max_email_sender_rules').fetchone()[0]==25;c.close()
    run(0);assert len(calls)==25 and reconcile(connect)==0
    # Existing confirmed intent without the original evidence must not be adopted.
    key,_=expected(make(0));c=connect();c.execute('DELETE FROM email_rule_provenance WHERE operation_key=?',(key,));c.commit();c.close()
    try:run(0)
    except ValueError:pass
    else:raise AssertionError('missing provenance adopted')
    assert len(calls)==25
    # Contradictory stored receipt cannot update bookkeeping.
    run(26);key,_=expected(make(26));c=connect();c.execute('UPDATE email_action_intents SET receipt_json=? WHERE operation_key=?',(json.dumps({'trashed':True,'id':'wrong'}),key));c.commit();c.close()
    try:reconcile(connect)
    except ValueError:pass
    else:raise AssertionError('bad receipt accepted')
    c=connect();assert c.execute('SELECT applied FROM email_rule_provenance WHERE operation_key=?',(key,)).fetchone()[0]==0
    assert c.execute('SELECT match_count FROM max_email_sender_rules').fetchone()[0]==25;c.close()
print(json.dumps({'status':'passed','provenance_committed_before_callback':True,'body_excluded':True,'reconciliation_batches':[20,5,0],'repeat_no_effect':True,'legacy_missing_evidence_held':True,'contradictory_receipt_held':True,'real_provider_calls':0}))
