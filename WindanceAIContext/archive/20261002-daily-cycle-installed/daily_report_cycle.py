"""At most one old-request query plus one current-day submission per cycle."""
import math,time
from daily_report_journal import run_daily

def run_daily_cycle(path,namespace,day,recipient,render,transport,*,seconds=150,clock=time.monotonic):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 1<=seconds<=150:
        raise ValueError('invalid_cycle_budget')
    deadline=clock()+seconds
    def bounded_transport(to,body,key,*,mode):
        remaining=deadline-clock()
        if remaining<1:return {'ok':False,'status':'unavailable','retry_action':'query_same_request_only'}
        return transport(to,body,key,mode=mode,budget_seconds=min(75,remaining))
    result=run_daily(path,namespace,day,recipient,render,bounded_transport)
    if result.get('status')!='previous_verified':return result
    if deadline-clock()<1:return {'status':'held','reason':'cycle_budget_exhausted'}
    # run_daily queries any remaining older attempt before creating today's
    # snapshot; no unbounded backlog loop, and no repeat of uncertain sends.
    return run_daily(path,namespace,day,recipient,render,bounded_transport)
