import json,subprocess,time
from outbox_wire_protocol import parse_response

payload={'to':'synthetic-owner','chunks':['synthetic-private-body'],'sms':False};key='synthetic-wire-key'
results=[]
for case,mode,status,code in (('legacy','query','legacy_submission',12),('legacy','submit','legacy_submission',12),
                            ('verified','query','verified_delivery',0),('queued','query','unknown',14)):
    command=['/usr/bin/ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','SAL','/usr/bin/python3','-B',
             '/tmp/outbox_protocol_cli.py','--root','/tmp/windance-wire-ssh-20261002/'+case,
             '--mode',mode,'--wait-seconds','0.5']
    started=time.monotonic()
    result=subprocess.run(command,input=json.dumps({'key':key,'payload':payload}),text=True,capture_output=True,timeout=15)
    elapsed=time.monotonic()-started
    assert result.returncode==code,(case,result.returncode)
    outcome=parse_response(result.stdout,result.returncode,key,payload)
    assert outcome['status']==status,(case,outcome)
    assert not result.stderr,(case,'unexpected_stderr')
    results.append({'case':case,'mode':mode,'status':status,'exit_code':code,'seconds':round(elapsed,3)})
print(json.dumps({'status':'passed','cases':results,'actual_ssh':True,'real_sends':0}))
