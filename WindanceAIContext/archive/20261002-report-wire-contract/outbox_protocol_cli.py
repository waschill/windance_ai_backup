"""Staged trusted SSH endpoint. Explicit root/mode; private request on stdin."""
import argparse,json,sys
from bounded_outbox_client import submit_and_wait
from bounded_outbox_status import query
from outbox_wire_protocol import envelope,CODES

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--mode',required=True,choices=('submit','query'))
    args=parser.parse_args()
    raw=sys.stdin.buffer.read(2*1024*1024+1)
    if len(raw)>2*1024*1024:raise ValueError('input_cap')
    request=json.loads(raw)
    if type(request) is not dict or set(request)!={'key','payload'}:raise ValueError('invalid_request')
    action=submit_and_wait if args.mode=='submit' else query
    result=action(args.root,request['key'],request['payload'],seconds=55)
    response=envelope(request['key'],request['payload'],result)
    print(json.dumps(response),flush=True)
    return CODES[result['status']]

if __name__=='__main__':
    try:code=main()
    except Exception:code=15
    raise SystemExit(code)
