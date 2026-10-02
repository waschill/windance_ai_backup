import json,tempfile
from pathlib import Path
from daily_report_journal import provision,run_daily

receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
with tempfile.TemporaryDirectory(prefix='windance-daily-journal-') as tmp:
    path=Path(tmp)/'private.db';calls=[];renders=[]
    def render():renders.append(True);return 'synthetic body '+str(len(renders))
    def uncertain(recipient,body,key,**kwargs):calls.append((body,key,kwargs['mode']));return {'ok':False,'status':'unknown'}
    def confirmed(recipient,body,key,**kwargs):calls.append((body,key,kwargs['mode']));return receipt
    assert run_daily(path,'sentinel-router','2026-10-02','synthetic-owner',render,uncertain)['reason']=='history_missing'
    assert not path.exists()
    provision(path)
    assert run_daily(path,'sentinel-router','2026-10-02','synthetic-owner',render,uncertain)['status']=='held'
    assert calls==[('synthetic body 1','sentinel-router:2026-10-02','submit')]
    assert run_daily(path,'sentinel-router','2026-10-03','synthetic-owner',render,confirmed)['status']=='previous_verified'
    assert calls[-1]==('synthetic body 1','sentinel-router:2026-10-02','query') and len(renders)==1
    assert run_daily(path,'sentinel-router','2026-10-03','synthetic-owner',render,confirmed)['status']=='verified'
    assert calls[-1]==('synthetic body 2','sentinel-router:2026-10-03','submit')
    before=list(calls)
    assert run_daily(path,'sentinel-router','2026-10-03','synthetic-owner',render,confirmed)['status']=='verified'
    assert calls==before and len(renders)==2
    assert run_daily(path,'sentinel-router','2026-10-03','other-owner',render,confirmed)['reason']=='recipient_changed'
    try:provision(path)
    except FileExistsError:pass
    else:raise AssertionError('history overwritten')
print(json.dumps({'status':'passed','missing_history_holds':True,'midnight_retains_body_key':True,'retry_query_only':True,'one_transport_per_run':True,'completed_no_resend':True,'recipient_change_holds':True,'real_sends':0}))
