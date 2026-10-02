"""Bounded read-only receipt polling; deliberately has no send capability."""
import math
import time


def await_receipt(probe,*,budget_seconds=30,poll_seconds=0.5,clock=time.monotonic,sleep=time.sleep):
    if (type(budget_seconds) not in (int,float) or not math.isfinite(budget_seconds) or not 0<budget_seconds<=60
        or type(poll_seconds) not in (int,float) or not math.isfinite(poll_seconds) or not 0<poll_seconds<=5):
        return {'status':'unavailable','reason':'invalid_wait_budget'}
    deadline=clock()+budget_seconds
    while True:
        remaining=deadline-clock()
        if remaining<=0:
            return {'status':'unconfirmed','reason':'delivery_wait_expired'}
        result=probe(min(15,remaining))
        if clock()>deadline:
            return {'status':'unconfirmed','reason':'delivery_wait_expired'}
        # Repeat observation only for expected asynchronous appearance/delivery.
        if (result.get('status')!='unconfirmed' or
            result.get('reason') not in ('no_exact_direct_message','delivery_flags_incomplete')):
            return result
        remaining=deadline-clock()
        if remaining<=0:
            return {'status':'unconfirmed','reason':'delivery_wait_expired'}
        sleep(min(poll_seconds,remaining))
