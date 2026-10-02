import hashlib,json,sqlite3,tempfile
from pathlib import Path
from task_report_journal import provision
from task_report_status import status
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'reports.db'
    assert status(p,'id')['state']=='history_unavailable'
    assert status(p,'id','delivered')=={'state':'legacy_recorded','independent_receipt':False}
    provision(p)
    with sqlite3.connect(p) as c:
        for state in ('ready','attempting','verified'):
            c.execute('INSERT INTO reports VALUES(?,?,?,?)',(state,'PRIVATE_RECIPIENT','PRIVATE_BODY',state))
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    observations=[status(p,key) for key in ('ready','attempting','verified','missing')]
    assert [o['state'] for o in observations]==['pending','unconfirmed','verified','not_recorded']
    assert [o['independent_receipt'] for o in observations]==[False,False,True,False]
    assert status(p,'legacy','failed')['state']=='legacy_unreconciled'
    assert 'PRIVATE' not in json.dumps(observations)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==before
print(json.dumps({'status':'passed','read_only':True,'private_content_absent':True,'legacy_not_upgraded':True}))
