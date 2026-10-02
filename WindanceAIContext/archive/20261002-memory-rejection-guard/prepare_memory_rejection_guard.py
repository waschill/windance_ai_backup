"""Stage a content-free rejection before audit/forwarding; no production edits."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
path=Path('/Users/herald/services/agent-harness/agent_harness.py');original=path.read_bytes();source=original.decode()
assert hashlib.sha256(original).hexdigest()=='4e0b60a2d51fa6d08c28f940a6a0566f756bc257bd864f89cf3272fd92fbc26e'
old='audit("memory_rejected_secret_like", {"source": source, "preview": text[:300]})'
assert source.count(old)==1
source=source.replace(old,'audit("memory_rejected_secret_like", {"reason": "secret_like_memory_content"})')
tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='message_sync')
body=ast.get_source_segment(source,node)
old='    text = payload.message.strip()\n'
assert body.count(old)==1
new=old+'''    memory_content = parse_remember_command(text)
    if memory_content is not None and memory_looks_secret(memory_content):
        audit("memory_rejected_secret_like", {"reason": "secret_like_memory_content"})
        return {"reply": "I did not store that because it looks like a password, token, key, or code. Keep secrets in the proper config file, not memory.", "provider": "deterministic", "model": "memory-guard"}
'''
source=source.replace(body,body.replace(old,new));ast.parse(source)
(root/'harness-memory-guard-candidate.py').write_text(source)
(root/'harness-memory-guard-candidate.py').chmod(0o600)
before=ast.parse(original.decode());after=ast.parse(source)
def unchanged(tree):return [ast.dump(n,include_attributes=False) for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name not in ['message_sync','remember_text']]
assert unchanged(before)==unchanged(after)
print(json.dumps({'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'changed_functions':['message_sync','remember_text'],'production_changed':False}))
