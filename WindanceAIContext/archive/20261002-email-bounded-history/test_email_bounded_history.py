"""Large synthetic history, finite result set, global holds and indexed lookup."""
import json, sqlite3, tempfile
from contextlib import closing
from pathlib import Path
from email_action_intent import install, operation_key, report_state

with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'fixture.db'
    def connect():return sqlite3.connect(path)
    with closing(connect()) as c:
        install(c)
        c.executemany('INSERT INTO email_action_intents(operation_key,request_sha256,action,state) VALUES(?,?,?,?)',[(operation_key('william',f'fixture-{i}'),'synthetic','draft','unconfirmed' if i%10==0 else 'confirmed') for i in range(10000)])
        c.commit()
    result=report_state(connect,'william',['fixture-0','fixture-9999','absent','fixture-0'])
    assert result=={'keys':{operation_key('william','fixture-0'),operation_key('william','fixture-9999')},'unconfirmed':1000}
    assert report_state(connect,'william',[])=={'keys':set(),'unconfirmed':1000}
    assert len(report_state(connect,'william',[f'fixture-{i}' for i in range(50)])['keys'])==50
    for owner,ids in [('shawn',[]),('william',['x']*51),('william',[None]),('william','fixture')]:
        try:report_state(lambda:(_ for _ in ()).throw(AssertionError('Must reject before DB')),owner,ids)
        except ValueError:pass
        else:raise AssertionError('Invalid scope/input accepted')
    with closing(connect()) as c:
        plan=c.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM email_action_intents WHERE state='unconfirmed'").fetchall()
        assert any('COVERING INDEX email_action_intents_state' in r[3] for r in plan)
        assert c.execute('SELECT COUNT(*) FROM email_action_intents').fetchone()[0]==10000
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
print(json.dumps({'synthetic_history_rows':10000,'global_unconfirmed_count':1000,'maximum_report_keys':50,'empty_inbox_preserves_holds':True,'state_count_uses_covering_index':True,'invalid_inputs_rejected_before_database':4,'actual_mailbox_calls':0,'production_changes':False,'limits':'Bounds returned keys and Python allocation; aggregate count still scales with held records. No global deadline or cross-path admission guarantee.'}))
