"""Container-local read-only lab predicates; prints only safe counts and flags."""
import ast,hashlib,json,os,sqlite3
from pathlib import Path
db=sqlite3.connect('file:/app/backend/data/webui.db?mode=ro',uri=True)
db.execute('PRAGMA query_only=ON')
counts={table:db.execute('SELECT count(*) FROM "'+table+'"').fetchone()[0] for table in ('user','chat','file','knowledge','memory','function','tool')}
assert all(v==0 for v in counts.values()),'Lab is no longer empty'
columns=[r[1] for r in db.execute('pragma table_info(config)')]
flags={r[0]:json.loads(r[1]) for r in db.execute("SELECT key,value FROM config WHERE key IN ('ui.enable_signup','ui.enable_login_form')")}
source=Path('/app/backend/open_webui/env.py').read_text()
assignment=[ast.unparse(n) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ENABLE_INITIAL_ADMIN_SIGNUP' for t in n.targets)]
processes=[]
for p in Path('/proc').glob('[0-9]*'):
    try:
        cmd=(p/'cmdline').read_bytes()
        if b'uvicorn' not in cmd or b'open_webui.main:app' not in cmd:continue
        env=dict(item.split(b'=',1) for item in (p/'environ').read_bytes().split(b'\0') if b'=' in item)
        value=env.get(b'ENABLE_INITIAL_ADMIN_SIGNUP',b'false')
        processes.append({'pid':int(p.name),'initial_admin_override':value.lower()==b'true'})
    except (FileNotFoundError,ProcessLookupError):pass
assert processes,'Server process not found'
print(json.dumps({'counts':counts,'flags':flags,'config_columns':columns,'initial_admin_source':assignment,'server_processes':processes,'initial_admin_override_false':all(not p['initial_admin_override'] for p in processes),'auth_source_sha256':hashlib.sha256(Path('/app/backend/open_webui/routers/auths.py').read_bytes()).hexdigest()}))
