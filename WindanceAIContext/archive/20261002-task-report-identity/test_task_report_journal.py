import json,sqlite3,tempfile
from pathlib import Path
from task_report_journal import provision,run_task
receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
def forbidden(*a,**k):raise AssertionError('unexpected effect')
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'reports.db'
    assert run_task(p,'task:william','synthetic-owner',forbidden,forbidden,forbidden)['reason']=='history_missing'
    provision(p)
    for prior in (True,None):
        assert run_task(p,'legacy','synthetic-owner',forbidden,lambda:prior,forbidden)['reason']=='legacy_history_unreconciled'
    calls=[]
    def uncertain(to,body,key,**kw):calls.append((to,body,key,kw['mode']));return {'ok':False}
    assert run_task(p,'task:william','synthetic-owner',lambda:'original report',lambda:False,uncertain)['status']=='held'
    # A changed result is not rendered and cannot acquire a new delivery key.
    assert run_task(p,'task:william','synthetic-owner',forbidden,forbidden,uncertain)['status']=='held'
    assert calls[0][:3]==calls[1][:3] and [x[3] for x in calls]==['submit','query']
    assert run_task(p,'task:william','different-owner',forbidden,forbidden,forbidden)['reason']=='recipient_changed'
    def confirmed(to,body,key,**kw):
        assert (to,body,key)==calls[0][:3] and kw['mode']=='query';return receipt
    assert run_task(p,'task:william','synthetic-owner',forbidden,forbidden,confirmed)=={'status':'verified'}
    assert run_task(p,'task:william','synthetic-owner',forbidden,forbidden,forbidden)=={'status':'verified'}
    with sqlite3.connect(p) as c:assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==1
print(json.dumps({'status':'passed','original_report_key_retained':True,'uncertain_query_only':True,'legacy_not_adopted':True,'recipient_change_held':True,'verified_no_replay':True,'real_sends':0}))
