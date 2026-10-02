"""Guarded two-host source rollout. No send, schedule change or Odoo mutation."""
import ast,datetime as dt,hashlib,json,os,plistlib,re,shutil,sqlite3,subprocess,sys,time,urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

host,mode=sys.argv[1:]
assert host=='HERALD', 'This rollout is HERALD only'
TABLES=['staff_tasks','staff_task_runs','staff_task_deliveries','staff_task_revisions','email_report_active','max_email_report_refs','email_autonomy_actions','approvals']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ro(p):return sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
def hashes(c):return {t:hashlib.sha256(json.dumps(c.execute('select * from '+t+' order by rowid').fetchall(),ensure_ascii=False).encode()).hexdigest() for t in TABLES}
assert 5<=dt.datetime.now(ZoneInfo('America/Denver')).hour<22
if host=='HERALD':
    home=Path('/Users/herald');stage=home/'services/memory-rejection-20261002';live=home/'services/agent-harness/agent_harness.py'
    plist=home/'Library/LaunchAgents/com.windance.agent-harness.plist'
    old='4e0b60a2d51fa6d08c28f940a6a0566f756bc257bd864f89cf3272fd92fbc26e';new='9865597bda4368784beac015dbcec712a271889395e9fcebf788c60b636774d4'
elif host=='SAL':
    home=Path('/Users/zuzu');stage=home/'backups/invoice-format-candidate-20261002';live=home/'bin/ledger_unpaid_invoice_report.py'
    plist=home/'Library/LaunchAgents/com.windance.ledger-unpaid-invoices.plist'
    old='e97253109a085b974c917965c8213a617c8ced7a01741f014162ea09da8f529e';new='ecd3ae83ff085921bd4fb799be932e5a920cd4b4db4a29a3be3a6b0a7760a2bf'
else:raise ValueError('Invalid host')
backup=home/'backups/memory-rejection-deploy-20261002T0123Z'
assert sha(live)==old and sha(stage/'candidate.private.py')==new
ast.parse((stage/'candidate.private.py').read_text())
if host=='SAL':
    assert (home/'services/windance-supervisor/PAUSED').exists()
    for label in ['com.windance.supervisor','com.windance.supervisor-review']:
        assert subprocess.run(['launchctl','print',f'gui/{os.getuid()}/{label}'],capture_output=True).returncode!=0
    status=subprocess.run(['launchctl','print',f'gui/{os.getuid()}/com.windance.ledger-unpaid-invoices'],capture_output=True,text=True,check=True).stdout
    assert re.search(r'(?m)^\s*state = not running\s*$',status)
    assert plistlib.loads(plist.read_bytes())['StartCalendarInterval']=={'Hour':8,'Minute':10}
    protected={}
else:
    assert subprocess.run(['ssh','SAL','/bin/test','-f','/Users/zuzu/services/windance-supervisor/PAUSED'],capture_output=True).returncode==0
    with urllib.request.urlopen('http://127.0.0.1:8793/health',timeout=5) as r:bridge=json.load(r)
    assert bridge['active']==0 and bridge['queued']==0
    with ro(home/'.local/share/vega-manager/manager.db') as c:
        assert c.execute("SELECT count(*) FROM messages WHERE status IN ('queued','submitted','execution_uncertain')").fetchone()[0]==0
        assert c.execute("SELECT count(*) FROM projects WHERE status IN ('active','review','delivery')").fetchone()[0]==0
    database=home/'.local/share/agent-harness/harness.db'
    with ro(database) as c:
        assert c.execute("SELECT count(*) FROM staff_tasks WHERE status IN ('pending','running','dispatching')").fetchone()[0]==0
        protected=hashes(c)
if mode=='backup':
    backup.mkdir(mode=0o700,exist_ok=False)
    for name,p in {'original.private.py':live,'candidate.private.py':stage/'candidate.private.py','service.plist':plist}.items():
        shutil.copy2(p,backup/name);(backup/name).chmod(0o600);assert sha(p)==sha(backup/name)
    if host=='HERALD':
        with ro(database) as c,sqlite3.connect(backup/'harness.db') as b:
            c.backup(b);assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert hashes(b)==protected
        shutil.copy2(backup/'harness.db',backup/'cold.db')
        with sqlite3.connect('file:'+str(backup/'cold.db')+'?immutable=1',uri=True) as c:
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and hashes(c)==protected
        for name in ['harness.db','cold.db']:(backup/name).chmod(0o600)
    receipt={'host':host,'backup':str(backup),'files':{name:sha(backup/name) for name in (['original.private.py','candidate.private.py','service.plist']+(['harness.db','cold.db'] if host=='HERALD' else []))},'protected_tables':protected,'cold_verified':True}
    (backup/'backup-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
elif mode=='deploy':
    receipt=json.loads((backup/'backup-receipt.json').read_text())
    assert all(sha(backup/n)==h for n,h in receipt['files'].items())
    assert sha(plist)==receipt['files']['service.plist'] and protected==receipt['protected_tables']
    temporary=live.with_name(live.name+'.memory-rejection-new')
    with temporary.open('xb') as f:f.write((stage/'candidate.private.py').read_bytes());f.flush();os.fsync(f.fileno())
    temporary.chmod(live.stat().st_mode & 0o777);os.replace(temporary,live)
    if host=='HERALD':
        subprocess.run(['launchctl','kickstart','-k','user/501/com.windance.agent-harness'],check=True,capture_output=True)
        healthy=False
        for _ in range(30):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8791/health',timeout=2) as r:healthy=r.status==200
                if healthy:break
            except Exception:pass
            time.sleep(1)
        assert healthy,'Installed source needs recovery; do not replay tasks'
        with ro(database) as c:assert hashes(c)==protected
    assert sha(live)==new and sha(plist)==receipt['files']['service.plist']
    out={'host':host,'source_sha256':sha(live),'service_definition_unchanged':True,'protected_tables_unchanged':True,
         'harness_health_200':host=='HERALD','scheduler_restarted':False,'manual_send':False,'backup':str(backup)}
    (backup/'deployment-receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
else:raise ValueError('Invalid mode')


