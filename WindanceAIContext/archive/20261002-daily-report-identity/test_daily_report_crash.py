import json,os,subprocess,sys,tempfile
from pathlib import Path
from daily_report_journal import provision,run_daily

if sys.argv[1:2]==['--child']:
    def crash(*args,**kwargs):os._exit(73)
    run_daily(Path(sys.argv[2]),'sentinel-router','2026-10-02','synthetic-owner',lambda:'synthetic original',crash)
    raise AssertionError('crash missing')
with tempfile.TemporaryDirectory(prefix='windance-daily-crash-') as tmp:
    path=Path(tmp)/'reports.db';provision(path)
    child=subprocess.run([sys.executable,'-B',__file__,'--child',str(path)],capture_output=True,timeout=3)
    assert child.returncode==73
    calls=[]
    def query(recipient,body,key,**kwargs):
        calls.append((body,key,kwargs['mode']))
        return {'ok':False,'status':'unknown'}
    def forbid_render():raise AssertionError('snapshot regenerated')
    for day in ('2026-10-02','2026-10-03'):
        assert run_daily(path,'sentinel-router',day,'synthetic-owner',forbid_render,query)['status']=='held'
    assert calls==[('synthetic original','sentinel-router:2026-10-02','query')]*2
print(json.dumps({'status':'passed','process_crash_reopens_query_only':True,'midnight_no_new_submission':True,'real_sends':0}))
