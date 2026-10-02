"""Synthetic actual-function regression. Never print or store submitted contents."""
from __future__ import annotations
import ast,json,re,types,__future__
from pathlib import Path
root=Path(__file__).resolve().parent
original=Path('/Users/herald/services/agent-harness/agent_harness.py').read_text()
candidate=(root/'harness-memory-guard-candidate.py').read_text()
marker='SYNTHETIC_REJECTION_MARKER_ABC'
def functions(source):
 tree=ast.parse(source);nodes=[]
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in ['remember_text','message_sync','parse_remember_command','memory_looks_secret']:
   node.decorator_list=[];nodes.append(node)
 module=ast.Module(body=nodes,type_ignores=[]);ast.fix_missing_locations(module)
 return compile(module,'actual-functions','exec',flags=__future__.annotations.compiler_flag)
class AuditReached(Exception):pass
def forbidden(*args,**kwargs):raise AssertionError('Unexpected storage or external effect')
def setup(source,stop_incoming=False):
 audits=[]
 def audit(kind,body):
  audits.append((kind,body))
  if stop_incoming and kind=='incoming_message':raise AuditReached()
 ns={'re':re,'audit':audit,'require_token':lambda *args,**kwargs:None,'sanitize_memory_text':lambda text:text.strip(),'upsert_memory':forbidden,
     'mirror_to_hermes_memory':forbidden,'redact_approval_auth_word':lambda t:t,'redact_level8_code':lambda t:t}
 exec(functions(source),ns)
 return ns,audits
o,a=setup(original);o['remember_text']('password: '+marker,'fixture')
assert marker in json.dumps(a)
c,a=setup(candidate);reply=c['remember_text']('password: '+marker,'fixture')
assert marker not in json.dumps(a) and marker not in str(reply)
checked=0
for prefix in ['remember this: ','please remember that ','save ','commit this: ']:
 command=prefix+'password: '+marker+(' to memory' if prefix=='save ' else '')
 payload=types.SimpleNamespace(message=command,user='William',channel='vega-internal',request_id='fixture')
 o,logs=setup(original,True)
 try:o['message_sync'](payload,None)
 except AuditReached:pass
 else:raise AssertionError('Original incoming audit not reached')
 assert marker in json.dumps(logs)
 c,logs=setup(candidate,True);result=c['message_sync'](payload,None)
 assert result['model']=='memory-guard' and marker not in json.dumps(logs) and marker not in json.dumps(result)
 assert logs==[('memory_rejected_secret_like',{'reason':'secret_like_memory_content'})]
 checked+=1
c,logs=setup(candidate,True)
try:c['message_sync'](types.SimpleNamespace(message='remember this: synthetic non-secret preference',user='William',channel='fixture'),None)
except AuditReached:pass
else:raise AssertionError('Non-secret normal path changed')
print(json.dumps({'original_rejection_audit_leak_reproduced':True,'original_incoming_audit_leak_reproduced':True,
 'candidate_content_free_direct_rejection':True,'candidate_early_rejection_command_variants':checked,
 'benign_normal_path_preserved':True,'production_changes':False,'model_calls':0,'private_content_used':False,
 'limits':'Harness functions only; upstream persistence and legacy direct memory API remain separate'}))
