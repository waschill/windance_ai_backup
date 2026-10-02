"""Staged HERALD report transport; no fallback or retry under a new key."""
import json,subprocess
from outbox_wire_protocol import identity,parse_response

def send_report(recipient,message,key,*,mode='submit'):
    if (type(recipient) is not str or not recipient.strip() or len(recipient)>320 or
        type(message) is not str or not message.strip() or len(message)>20000 or mode not in ('submit','query')):
        raise ValueError('invalid_report')
    payload={'to':recipient.strip(),'chunks':[message.strip()],'sms':False}
    identity(key,payload)  # Missing key fails before SSH; never invent a retry key.
    command=['/usr/bin/ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','SAL','/usr/bin/python3',
             '/Users/zuzu/services/receipt-outbox/outbox_protocol_cli.py','--root',
             '/Users/zuzu/.local/share/windance-imessage-outbox','--mode',mode]
    try:
        result=subprocess.run(command,input=json.dumps({'key':key,'payload':payload}),
                              capture_output=True,text=True,timeout=75)
        outcome=parse_response(result.stdout,result.returncode,key,payload)
    except subprocess.TimeoutExpired:
        return {'ok':False,'status':'unknown','retry_action':'query_same_request_only'}
    except (ValueError,OSError):
        return {'ok':False,'status':'unavailable','retry_action':'query_same_request_only'}
    if outcome['status']!='verified_delivery':
        return {'ok':False,'status':outcome['status'],'retry_action':'query_same_request_only'}
    return {'ok':True,'transport':'imessage','chunks':outcome['chunks'],
            'receipt':{'version':2,'ok':True,'status':'delivered',
                       'evidence':'local_messages_flags','chunks':outcome['chunks']}}
