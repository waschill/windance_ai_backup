"""Read-only AST inventory. Reachability is not proof of guard ordering."""
import ast, collections, hashlib, json, sys
from pathlib import Path
source = Path(sys.argv[1])
raw = source.read_bytes()
tree = ast.parse(raw.decode('utf-8-sig'))
functions = {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def callees(node):
    out=set()
    for n in ast.walk(node):
        if not isinstance(n,ast.Call): continue
        if isinstance(n.func,ast.Name): out.add(n.func.id)
        if isinstance(n.func,ast.Attribute) and n.func.attr=='to_thread' and n.args and isinstance(n.args[0],ast.Name): out.add(n.args[0].id)
    return out
def guards(name):
    todo=[name]; seen=set(); found=set()
    while todo:
        item=todo.pop()
        if item in seen: continue
        seen.add(item)
        if item in ('require_token','require_hal_delegation_worker'):
            found.add(item); continue
        if item in functions: todo.extend(callees(functions[item])-seen)
    return sorted(found)
rows=[]
for name,node in functions.items():
    for d in node.decorator_list:
        if not isinstance(d,ast.Call) or not isinstance(d.func,ast.Attribute): continue
        if not isinstance(d.func.value,ast.Name) or d.func.value.id!='app': continue
        if d.func.attr not in {'get','post','put','patch','delete','options','head'}: continue
        path=ast.literal_eval(d.args[0])
        rows.append(dict(method=d.func.attr,path=path,handler=name,middleware='health exception' if path=='/health' else 'trusted source or configured bearer',reachable_guards=guards(name)))
result=dict(source_sha256=hashlib.sha256(raw).hexdigest(),http_routes=len(rows),routes=rows,limits='Static reachability does not prove guard execution, ordering, proxy behavior, or per-user identity. Middleware and startup decorators are excluded.')
print(json.dumps(result,indent=2))
