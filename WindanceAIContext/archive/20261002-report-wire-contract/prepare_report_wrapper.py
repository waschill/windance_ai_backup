"""Prepare inert private wrapper; preserves the pinned original recipient."""
import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
source=root/'windance_report_send.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'
tree=ast.parse(source.read_text());recipients=[]
for node in ast.walk(tree):
    if isinstance(node,ast.Dict):
        for key,value in zip(node.keys,node.values):
            if isinstance(key,ast.Constant) and key.value=='to' and isinstance(value,ast.Constant):recipients.append(value.value)
assert len(recipients)==1 and type(recipients[0]) is str
candidate=root/'windance_report_send_candidate_r2.py'
assert not candidate.exists()
candidate.write_text('''import json,os,sys
from receipt_report_transport import send_report

def main():
    message=sys.stdin.read(20001)
    if len(message)>20000:raise ValueError('report_too_large')
    message=message.strip()
    key=os.environ.get('WINDANCE_DELIVERY_KEY','').strip()
    result=send_report(RECIPIENT,message,key)
    print(json.dumps(result))
    return 0 if result.get('ok') is True else 1

if __name__=='__main__':
    try:code=main()
    except Exception:code=1
    raise SystemExit(code)
'''.replace('RECIPIENT',repr(recipients[0])))
print('candidate_sha256='+hashlib.sha256(candidate.read_bytes()).hexdigest())
