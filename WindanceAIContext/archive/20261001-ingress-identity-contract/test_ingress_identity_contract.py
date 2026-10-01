"""Actual middleware in isolation; no HTTP request, database or dispatch."""
import ast
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

p=Path('/Users/herald/services/agent-harness/agent_harness.py')
s=p.read_text();t=ast.parse(s)
node=next(n for n in t.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='protect_mutating_and_control_routes')
node.decorator_list=[]
namespace={'Request':object,'TRUSTED_HARNESS_CLIENTS':{'fixture-trusted'},'HARNESS_TOKEN':'fixture-only-token',
           'JSONResponse':lambda body,status_code: {'status':status_code}}
exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-middleware>','exec'),namespace)
async def run():
    results=[]
    for host,auth,owner,expected in [('fixture-trusted','','william',200),('fixture-trusted','','shawn',200),
      ('fixture-untrusted','Bearer fixture-only-token','william',200),
      ('fixture-untrusted','Bearer fixture-only-token','shawn',200),('fixture-untrusted','','william',401)]:
        request=SimpleNamespace(url=SimpleNamespace(path='/message'),client=SimpleNamespace(host=host),
          headers={'authorization':auth},body={'user':owner})
        async def downstream(r):return {'status':200,'claimed_owner':r.body['user']}
        result=await namespace[node.name](request,downstream)
        assert result['status']==expected
        results.append({'trusted_host':host=='fixture-trusted','credential_present':bool(auth),
                        'claimed_owner':owner,'passed_middleware':expected==200})
    return results
results=asyncio.run(run())
print(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cases':results,
 'finding':'Service authorization does not bind the claimed person. Downstream shown here is a synthetic marker, not a real action.',
 'production_requests':0,'model_calls':0,'dispatches':0},indent=2))
