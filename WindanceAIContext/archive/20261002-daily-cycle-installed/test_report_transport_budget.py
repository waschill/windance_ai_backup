import json,subprocess
from types import SimpleNamespace
import receipt_report_transport as transport
calls=[]
def run(command,**kwargs):
    calls.append(True)
    assert kwargs['timeout']==3 and command[command.index('--wait-seconds')+1]=='0.1'
    raise subprocess.TimeoutExpired(command,3)
transport.subprocess=SimpleNamespace(run=run,TimeoutExpired=subprocess.TimeoutExpired)
assert transport.send_report('synthetic-owner','synthetic report','key',budget_seconds=3)['status']=='unknown'
for invalid in (0,76,float('nan'),True):
    try:transport.send_report('synthetic-owner','synthetic report','key',budget_seconds=invalid)
    except ValueError:pass
    else:raise AssertionError('invalid budget accepted')
assert len(calls)==1
print(json.dumps({'status':'passed','relative_endpoint_budget':True,'invalid_budget_no_transport':True,'real_sends':0}))
