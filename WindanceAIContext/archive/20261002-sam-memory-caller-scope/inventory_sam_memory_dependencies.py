"""Static source/call metadata and service state only; no imports, DB or API calls."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
root=Path('/home/williamschilling/services/sam-schedule')
records=[]
for path in sorted(root.glob('*.py')):
    if any(word in path.name for word in ['test_','backup','before','candidate']):continue
    try:
        raw=path.read_bytes();tree=ast.parse(raw.decode())
    except (OSError,UnicodeError,SyntaxError):continue
    routes=set();functions=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Constant) and isinstance(node.value,str):
            value=node.value
            if re.fullmatch(r'/(?:memory|sam|training|health|api)[A-Za-z0-9_/{}/.?:=-]*',value):routes.add(value)
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            endpoint_literals=sorted({n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and isinstance(n.value,str)
                 and re.fullmatch(r'/(?:memory|sam|training)[A-Za-z0-9_/{}/.-]*',n.value)})
            if endpoint_literals:
                kinds=[]
                for item in ast.walk(node):
                    if isinstance(item,ast.Dict):
                        for key,value in zip(item.keys,item.values):
                            if isinstance(key,ast.Constant) and key.value=='kind' and isinstance(value,ast.Constant) and isinstance(value.value,str) and re.fullmatch(r'[a-zA-Z0-9_-]+',value.value):kinds.append(value.value)
                functions.append({'function':node.name,'line':node.lineno,'endpoint_literals':endpoint_literals,'literal_memory_kinds':sorted(set(kinds))})
    if routes or functions:records.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),
                                         'literal_routes':sorted(routes),'functions':functions})
states={}
for name in ['sam-schedule.service','sam-schedule-nightly.timer','sam-schedule-refresh.timer','sam-schedule-nightly.service','sam-schedule-refresh.service']:
    result=subprocess.run(['systemctl','show',name,'--property=LoadState,ActiveState,SubState'],capture_output=True,text=True,timeout=5)
    states[name]={k:v for line in result.stdout.splitlines() if '=' in line for k,v in [line.split('=',1)]}
    if name.endswith('.service'):
        start=subprocess.run(['systemctl','show',name,'--property=ExecStart','--value'],capture_output=True,text=True,timeout=5)
        states[name]['matching_source_paths']=[record['path'] for record in records if record['path'] in start.stdout]
print(json.dumps({'scope':'SAM top-level Python static references and named unit state only','records':records,
                  'units':states,'production_changes':False,'database_reads':0,'api_calls':0},indent=2))
