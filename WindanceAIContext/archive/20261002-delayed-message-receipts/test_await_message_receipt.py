import json
from await_message_receipt import await_receipt

class Clock:
    def __init__(self):self.now=0;self.calls=[]
    def clock(self):return self.now
    def sleep(self,seconds):self.now+=seconds

results=[]
for case in ('delayed','never','ambiguous','changed_store','probe_overrun'):
    fake=Clock()
    def probe(budget):
        fake.calls.append(budget)
        if case=='probe_overrun':
            fake.now+=budget+0.1
            return {'status':'delivered','evidence':'local_messages_flags','message_rowid':1}
        if case=='ambiguous':return {'status':'ambiguous','reason':'multiple_exact_messages'}
        if case=='changed_store':return {'status':'unconfirmed','reason':'message_store_changed'}
        if case=='delayed' and len(fake.calls)==3:return {'status':'delivered','evidence':'local_messages_flags','message_rowid':1}
        return {'status':'unconfirmed','reason':'delivery_flags_incomplete'}
    output=await_receipt(probe,budget_seconds=1,poll_seconds=0.2,clock=fake.clock,sleep=fake.sleep)
    assert (output['status']=='delivered')==(case=='delayed')
    if case in ('ambiguous','changed_store','probe_overrun'):assert len(fake.calls)==1
    if case in ('never','probe_overrun'):assert output['reason']=='delivery_wait_expired'
    assert all(0<x<=1 for x in fake.calls)
    results.append({'case':case,'calls':len(fake.calls),'status':output['status']})
for invalid in (0,-1,61,True,float('nan'),float('inf')):
    assert await_receipt(lambda _:None,budget_seconds=invalid)['reason']=='invalid_wait_budget'
print(json.dumps({'status':'passed','cases':results,'sends':0}))
