import ast,json,types
from pathlib import Path
s=Path('caller-contract-private/bridge.py').read_text(encoding='utf-8');t=ast.parse(s)
nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('send_max_message','run_once')]
assert len(nodes)==2
seen={};calls=[]
def send(args,**kwargs):
 calls.append({'key_supplied':'WINDANCE_DELIVERY_KEY' in kwargs.get('env',{})})
 return types.SimpleNamespace(returncode=1,stdout='synthetic unconfirmed')
ns={'subprocess':types.SimpleNamespace(run=send,PIPE=-1,STDOUT=-2),'ensure_dirs':lambda:None,
'fetch_staff_tasks':lambda:[{'id':'synthetic-task','status':'completed','updated_at':'fixed','title':'synthetic','assignee':'fixture'}],
'write_inbox':lambda tasks:None,'read_seen':lambda:dict(seen),'save_seen':lambda x:seen.update(x),'log':lambda text:None}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-bridge-functions','exec'),ns)
assert ns['run_once']()==0 and len(calls)==1 and seen
assert ns['run_once']()==0 and len(calls)==1
assert calls==[{'key_supplied':False}]
print(json.dumps({'failure_marked_seen_reproduced':True,'next_run_skips_failed_notice':True,'delivery_key_missing':True,'real_sends':0,'live_state_changed':False}))
