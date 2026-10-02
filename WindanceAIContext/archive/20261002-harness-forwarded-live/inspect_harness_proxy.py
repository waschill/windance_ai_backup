"""Read-only server proxy configuration metadata; no environments or secrets."""
import ast,hashlib,inspect,json,plistlib,subprocess
from pathlib import Path
import uvicorn
p=Path('/Users/herald/services/agent-harness/agent_harness.py')
raw=p.read_bytes();tree=ast.parse(raw)
safe={'host','port','proxy_headers','forwarded_allow_ips'}
calls=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='uvicorn' and n.func.attr=='run':
        info={}
        for k in n.keywords:
            if k.arg in safe:
                try:info[k.arg]=ast.literal_eval(k.value)
                except (ValueError,TypeError):info[k.arg]='dynamic expression'
        calls.append(info)
plists=[]
for f in Path('/Users/herald/Library/LaunchAgents').glob('*harness*.plist'):
    d=plistlib.loads(f.read_bytes());args=d.get('ProgramArguments',[])
    flags={}
    for i,a in enumerate(args):
        if a in ('--host','--port','--forwarded-allow-ips') and i+1<len(args):flags[a]=args[i+1]
        if a in ('--proxy-headers','--no-proxy-headers'):flags[a]=True
    env=d.get('EnvironmentVariables',{})
    plists.append({'name':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'proxy_flags':flags,'forwarded_allow_ips_env_present':'FORWARDED_ALLOW_IPS' in env,'harness_source_argument_present':str(p) in args})
signature=inspect.signature(uvicorn.Config)
defaults={k:str(signature.parameters[k].default) for k in ('proxy_headers','forwarded_allow_ips')}
print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'uvicorn_version':uvicorn.__version__,'source_run_options':calls,'config_defaults':defaults,'plists':plists,'limits':'Saved plist and source metadata, not running process environment or reverse proxy configuration.'},indent=2))
