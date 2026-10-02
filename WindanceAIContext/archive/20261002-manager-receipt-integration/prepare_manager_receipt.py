"""Build private inert manager candidate, preserving all other functions."""
import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
source=root/'manager.py';wrapper=root/'windance_report_send.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'
recipients=[v.value for n in ast.walk(ast.parse(wrapper.read_text())) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='to' and isinstance(v,ast.Constant)]
assert len(recipients)==1
text=source.read_text();tree=ast.parse(text);lines=text.splitlines(keepends=True)
node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='send')
old=''.join(lines[node.lineno-1:node.end_lineno]).replace('async def send(', 'async def send_legacy(',1)
new='''
async def send(text, key, owner="William"):
    valid_owner(owner)
    if owner == 'Shawn':
        return await send_legacy(text,key,owner)
    if owner != 'William':raise ValueError('unrecognized_report_owner')
    from manager_receipt_delivery import deliver
    from receipt_report_transport import send_report
    return await asyncio.to_thread(deliver,connect,RECIPIENT_VALUE,text,key,send_report)

'''.replace('RECIPIENT_VALUE',repr(recipients[0]))
candidate=''.join(lines[:node.lineno-1])+old+'\n'+new+''.join(lines[node.end_lineno:])
after=ast.parse(candidate)
def functions(t):return {n.name:ast.dump(n) for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name not in ('send','send_legacy')}
assert functions(tree)==functions(after)
target=root/'manager_receipt_candidate.py'
with target.open('x',encoding='utf-8',newline='') as f:f.write(candidate)
print('candidate_sha256='+hashlib.sha256(target.read_bytes()).hexdigest())
