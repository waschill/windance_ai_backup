import json,sqlite3,tempfile
from pathlib import Path
from daily_report_journal import provision,run_daily
from daily_report_cycle import run_daily_cycle
receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
results=[]
with tempfile.TemporaryDirectory() as tmp:
    for case in ('shrinking_budget','expired','unresolved'):
        path=Path(tmp)/(case+'.db');provision(path)
        run_daily(path,'fixture','2026-10-01','synthetic-owner',lambda:'original',lambda *a,**kw:{'ok':False})
        ticks=[0];calls=[];renders=[]
        def render():renders.append(True);return 'today'
        def send(to,body,key,**kw):
            calls.append((body,key,kw['mode'],kw['budget_seconds']))
            if kw['mode']=='query':
                ticks[0]=151 if case=='expired' else 110
                return {'ok':False} if case=='unresolved' else receipt
            return receipt
        result=run_daily_cycle(path,'fixture','2026-10-02','synthetic-owner',render,send,clock=lambda:ticks[0])
        if case=='shrinking_budget':
            assert result['status']=='verified' and len(renders)==1
            assert [c[2] for c in calls]==['query','submit'] and [c[3] for c in calls]==[75,40]
            assert calls[0][0]=='original' and calls[1][0]=='today'
        else:
            assert result['status']=='held' and len(calls)==1 and not renders
            with sqlite3.connect(path) as c:assert c.execute("SELECT COUNT(*) FROM reports WHERE day='2026-10-02'").fetchone()[0]==0
        results.append(case)
print(json.dumps({'status':'passed','cases':results,'new_submissions_per_cycle_at_most_one':True,'real_sends':0}))
