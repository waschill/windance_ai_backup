"""Extract only installed signup guard; no application import or user creation."""
import ast
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

path=Path('/app/backend/open_webui/routers/auths.py')
source=path.read_text()
function=next(n for n in ast.parse(source).body if isinstance(n,ast.AsyncFunctionDef) and n.name=='signup')
# Preserve the exact two leading guard statements, stop before email/registration.
assert isinstance(function.body[0],ast.Assign)
assert isinstance(function.body[1],ast.If)
guard=ast.AsyncFunctionDef(name='guard',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
                         body=function.body[:2]+[ast.Return(value=ast.Constant(True))],decorator_list=[])
code=compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),'<installed-signup-guard>','exec')
class Denied(Exception):
    def __init__(self,*args,**kwargs):pass
async def test(existing,signup,login,initial):
    class Users:
        @staticmethod
        async def has_users(**kwargs):return existing
    class Config:
        @staticmethod
        async def get(key):return {'ui.enable_signup':signup,'ui.enable_login_form':login}[key]
    ns={'Users':Users,'Config':Config,'WEBUI_AUTH':True,'ENABLE_INITIAL_ADMIN_SIGNUP':initial,
        'db':None,'HTTPException':Denied,'status':SimpleNamespace(HTTP_403_FORBIDDEN=403),
        'ERROR_MESSAGES':SimpleNamespace(ACCESS_PROHIBITED='synthetic')}
    exec(code,ns)
    try:return await ns['guard']()
    except Denied:return False
cases=[('signup false alone still permits first admin',False,False,True,False,True),
       ('both bootstrap and login disabled blocks first admin',False,False,False,False,False),
       ('bootstrap override permits first admin despite login disabled',False,False,False,True,True),
       ('signup false blocks subsequent accounts',True,False,True,False,False)]
for name,*values in cases:
    *inputs,expected=values
    assert asyncio.run(test(*inputs)) is expected,name
print(json.dumps({'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'passed':[c[0] for c in cases],
                  'registration_functions_called':0,'network_calls':0,'database_access':False,'production_changes':0}))
