"""Execute inside existing WebUI container: metadata only, read-only database."""
import datetime
import ast
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import urllib.request
import urllib.error

out = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
boolean_settings = ['WEBUI_AUTH','ENABLE_SIGNUP','ENABLE_LOGIN_FORM','ENABLE_API_KEY',
                    'ENABLE_PERSISTENT_CONFIG','ENABLE_COMMUNITY_SHARING','ENABLE_MESSAGE_RATING']
out['environment_booleans'] = {k:os.environ[k] for k in boolean_settings if k in os.environ and os.environ[k].lower() in ('true','false','0','1')}
out['trusted_auth_headers_configured'] = {k:bool(os.environ.get(k)) for k in ['WEBUI_AUTH_TRUSTED_EMAIL_HEADER','WEBUI_AUTH_TRUSTED_NAME_HEADER']}
path = Path('/app/backend/data/webui.db')
conn = sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
conn.execute('pragma query_only=ON');conn.execute('begin')
tables = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
out['metadata'] = {}
for table in ['user','chat','knowledge','file','memory','config','group','function','tool']:
    if table not in tables:continue
    columns = [r[1] for r in conn.execute('pragma table_info("'+table+'")')]
    record = {'columns':columns,'count':conn.execute('select count(*) from "'+table+'"').fetchone()[0]}
    if table=='user' and 'role' in columns:
        record['roles'] = dict(conn.execute('select role,count(*) from "user" group by role'))
    if table in ('knowledge','file','memory','chat') and 'user_id' in columns:
        record['distinct_owners'] = conn.execute('select count(distinct user_id) from "'+table+'"').fetchone()[0]
    out['metadata'][table]=record
if 'function' in tables:
    out['function_boundaries'] = []
    for kind,content,active,globally in conn.execute('select type,content,is_active,is_global from "function"'):
        body=str(content or '')
        item={'type':kind,'active':bool(active),'global':bool(globally),'source_sha256':hashlib.sha256(body.encode()).hexdigest()}
        try:
            tree=ast.parse(body)
            item['imports']=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module}|{alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names})
            item['class_names']=[n.name for n in tree.body if isinstance(n,ast.ClassDef)]
        except SyntaxError:item['parse']='not-python-or-invalid'
        out['function_boundaries'].append(item)
conn.close()
out['public_http'] = {}
for endpoint in ['/health','/api/config','/api/v1/chats/','/api/v1/users/']:
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080'+endpoint,timeout=5) as response:
            item={'status':response.status}
            if endpoint=='/api/config':
                data=json.load(response)
                item['version']=data.get('version')
                features=data.get('features',{})
                item['features']={k:v for k,v in features.items() if isinstance(v,bool)}
            out['public_http'][endpoint]=item
    except urllib.error.HTTPError as exc:out['public_http'][endpoint]={'status':exc.code}
    except Exception as exc:out['public_http'][endpoint]={'error_type':type(exc).__name__}
out.update(database_read_only=True,private_contents_exported=False,account_changes=0)
print(json.dumps(out))
