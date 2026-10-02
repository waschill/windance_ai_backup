import hashlib,json,sqlite3,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
from daily_report_journal import run_daily
source=root/'synthetic-reports.db';before=hashlib.sha256(source.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='windance-report-restore-') as tmp:
    restored=Path(tmp)/'reports.db'
    with sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True) as s,sqlite3.connect(str(restored)) as d:
        assert s.execute('PRAGMA integrity_check').fetchone()[0]=='ok';s.backup(d)
        assert d.execute('PRAGMA user_version').fetchone()[0]==2
        assert d.execute('SELECT state,report_available FROM reports ORDER BY namespace').fetchall()==[('verified',1),('attempting',0)]
    calls=[]
    def forbidden():raise AssertionError('rerendered')
    def query(recipient,body,key,**kwargs):calls.append(kwargs['mode']);return {'ok':False}
    assert run_daily(restored,'synthetic-held','2026-10-03','synthetic-owner',forbidden,query)['status']=='held'
    assert calls==['query']
    outcome=run_daily(restored,'synthetic-done','2026-10-02','synthetic-owner',forbidden,query)
    assert outcome['status']=='verified' and outcome['report_available'] is True and calls==['query']
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print(json.dumps({'status':'passed','cold_snapshot_retains_states':True,'uncertain_query_only':True,'completed_no_send':True,'snapshot_unchanged':True}))
