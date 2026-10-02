"""Source-only caller inventory. No imports or credential/header values exported."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import os
import plistlib
import subprocess
from urllib.parse import urlsplit

host=sys.argv[1]
if host=='HERALD':
    root=Path('/Users/herald/services')
    files=[p for d in root.iterdir() if d.is_dir() and not re.search(r'20\d{6}|stag|backup',d.name)
           for p in d.glob('*.py')]
elif host=='SAL': files=list(Path('/Users/zuzu/bin').glob('*.py'))
else: raise ValueError('Unexpected host')
records=[]
for p in files:
    if any(x in p.name for x in ['.before','.original','.staged','.host-context','.pre-','test_']) or p.name=='agent_harness.py':continue
    try:s=p.read_text();tree=ast.parse(s)
    except (OSError,UnicodeError,SyntaxError):continue
    if not any(x in s for x in ['8791','HARNESS_URL','HARNESS_BASE']):continue
    paths=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            v=n.value
            if v.startswith(('http://','https://')) and len(v)<300 and not any(c.isspace() for c in v):
                v=urlsplit(v).path
            if re.fullmatch(r'/(?:message|memory|memories|reflect|sam|training|reports|staff|health|briefing)[A-Za-z0-9_/{}/.-]*',v):paths.add(v)
    registrations=[]
    for plist in (Path.home()/'Library/LaunchAgents').glob('*.plist'):
        try:config=plistlib.loads(plist.read_bytes())
        except Exception:continue
        args=config.get('ProgramArguments',[])
        if str(p) not in args:continue
        label=config.get('Label','')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',label):continue
        states=[]
        for domain in ('user','gui'):
            result=subprocess.run(['launchctl','print',f'{domain}/{os.getuid()}/{label}'],capture_output=True,text=True)
            if result.returncode==0:
                match=re.search(r'(?m)^\s*state = ([^\r\n]+)',result.stdout)
                states.append({'domain':domain,'state':match.group(1) if match else 'registered'})
        registrations.append({'label':label,'loaded':states})
    records.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'direct_plist_matches':registrations,
                    'literal_paths':sorted(paths),'authorization_header_mentioned':bool(re.search(r'authorization',s,re.I))})
print(json.dumps({'host':host,'scope':'Top-level service source candidates, not proof of registration or complete dynamic call graph',
                  'records':records},indent=2))

