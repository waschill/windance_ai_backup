"""Read-only code metadata inventory, never emits recipient or payload literals."""
import ast
import hashlib
import json
import os
from pathlib import Path
import time
import sys

root=Path.home()
hits=[];examined=0;limited=False;start=time.monotonic()
needles=('send_imessage_payload.py','windance_report_send.py','windance-imessage-outbox')
skip={'.git','.venv','venv','node_modules','__pycache__','backups','archive','archives','site-packages','vendor'}
for top in ([Path(p) for p in sys.argv[1:]] or [root/'bin',root/'services']):
    for folder,dirs,files in os.walk(top):
        dirs[:]=[d for d in dirs if d not in skip and 'backup' not in d.lower() and not d.startswith('.')]
        if time.monotonic()-start>12 or examined>=3000:limited=True;break
        for name in files:
            if examined>=3000:limited=True;break
            if not name.endswith(('.py','.sh','.js')):continue
            path=Path(folder)/name
            try:
                if path.stat().st_size>1024*1024:continue
                content=path.read_bytes();examined+=1
                text=content.decode('utf-8')
            except (OSError,UnicodeError):continue
            matching=[needle for needle in needles if needle in text]
            if not matching:continue
            metadata={'path':str(path),'sha256':hashlib.sha256(content).hexdigest(),'references':matching,
                      'idempotency_reference':'idempotency_key' in text or 'WINDANCE_DELIVERY_KEY' in text,
                      'timeouts':[],'literal_sms_true':False}
            if name.endswith('.py'):
                try:
                    tree=ast.parse(text)
                    for node in ast.walk(tree):
                        if isinstance(node,ast.Call):
                            for kw in node.keywords:
                                if kw.arg=='timeout':
                                    value=kw.value.value if isinstance(kw.value,ast.Constant) and type(kw.value.value) in (int,float) else 'dynamic'
                                    owner=next((f.name for f in ast.walk(tree) if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.lineno<=node.lineno<=f.end_lineno),'<module>')
                                    metadata['timeouts'].append({'line':node.lineno,'function':owner,'seconds':value})
                        if isinstance(node,ast.Dict):
                            for key,value in zip(node.keys,node.values):
                                if isinstance(key,ast.Constant) and key.value=='sms' and isinstance(value,ast.Constant) and value.value is True:
                                    metadata['literal_sms_true']=True
                except SyntaxError:metadata['parse']='failed'
            hits.append(metadata)
        if limited:break
    if limited:break
print(json.dumps({'examined_source_files':examined,'limited':limited,'callers':hits,'seconds':round(time.monotonic()-start,3)}))
