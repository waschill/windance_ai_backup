"""Synthetic held/legacy/corrupt/missing schemas; no private fixture contents."""
import hashlib,json,sqlite3,tempfile
from unittest.mock import patch
from pathlib import Path
from email_recovery_status import inspect

with tempfile.TemporaryDirectory() as folder:
    p=Path(folder)/'fixture.db'
    assert inspect(p)['inspection']=='unknown' and not p.exists()
    c=sqlite3.connect(p)
    c.execute('CREATE TABLE approvals(id TEXT,action TEXT,status TEXT,payload_json TEXT,decision_note TEXT)')
    c.commit();c.close()
    assert inspect(p)['inspection']=='incomplete_schema'
    c=sqlite3.connect(p)
    for t in ('email_action_intents','email_approved_item_intents','email_undo_intents'):
        c.execute('CREATE TABLE '+t+'(state TEXT)')
        c.execute('INSERT INTO '+t+" VALUES('unconfirmed')")
    c.execute('CREATE TABLE email_mailbox_admission(operation_key TEXT)')
    c.execute("INSERT INTO email_mailbox_admission VALUES('PRIVATE_SENTINEL')")
    for i in range(25):
        c.execute('INSERT INTO approvals VALUES(?,?,?,?,?)',(f'PRIVATE_SENTINEL_{i}','gmail.send','executing','PRIVATE_SENTINEL','PRIVATE_SENTINEL'))
    c.execute("INSERT INTO approvals VALUES('secret','gmail.delete','uncertain','PRIVATE_SENTINEL','PRIVATE_SENTINEL')")
    c.commit();c.close()
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    report=inspect(p)
    assert report['inspection']=='complete' and report['recorded_mutation_hold']
    assert report['reservation_count']==1 and all(v==1 for v in report['unconfirmed_items'].values())
    assert report['approval_counts']=={'pending':0,'executing':25,'uncertain':1}
    assert len(report['held_approval_references'])==20 and report['references_truncated']
    assert 'PRIVATE_SENTINEL' not in json.dumps(report)
    assert before==hashlib.sha256(p.read_bytes()).hexdigest()
    c=sqlite3.connect(p)
    c.executemany('INSERT INTO approvals VALUES(?,?,?,?,?)',[(f'fixture-{i}','gmail.delete','pending','PRIVATE_SENTINEL','PRIVATE_SENTINEL') for i in range(1000)])
    c.commit();c.close()
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    calls=iter([0.0]+[10.0]*100)
    with patch('email_recovery_status.time.monotonic',side_effect=lambda:next(calls)):
        assert inspect(p,seconds=0.01)['inspection']=='unknown'
    assert before==hashlib.sha256(p.read_bytes()).hexdigest()
    c=sqlite3.connect(p);c.execute('DROP TABLE email_undo_intents');c.execute('CREATE TABLE email_undo_intents(wrong_column TEXT)');c.commit();c.close()
    assert inspect(p)['inspection']=='unknown'
print(json.dumps({'passed':['missing_not_created','legacy_incomplete','holds_and_approval_states','bounded_references','content_excluded','database_unchanged','deadline_interrupt_unknown','unsupported_schema_unknown'], 'mutation_calls':0}))
