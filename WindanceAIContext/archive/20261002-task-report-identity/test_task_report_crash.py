import json,os,subprocess,sys,tempfile
from pathlib import Path
from task_report_journal import provision,run_task
if len(sys.argv)>1:
    def die(*args,**kwargs):os._exit(73)
    run_task(Path(sys.argv[1]),'synthetic-task:william','synthetic-owner',lambda:'original report',lambda:False,die)
    raise AssertionError('crash not reached')
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'reports.db';provision(p)
    child=subprocess.run([sys.executable,'-B',__file__,str(p)],timeout=5)
    assert child.returncode==73
    def forbidden():raise AssertionError('snapshot recomputed')
    calls=[]
    def transport(to,body,key,**kw):
        calls.append(kw['mode']);assert body=='original report'
        return {'ok':False}
    assert run_task(p,'synthetic-task:william','synthetic-owner',forbidden,forbidden,transport)['status']=='held'
    assert calls==['query']
print(json.dumps({'status':'passed','process_crash_query_only':True,'real_sends':0,'power_loss_tested':False}))
