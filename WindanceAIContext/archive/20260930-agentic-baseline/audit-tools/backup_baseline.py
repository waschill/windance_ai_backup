"""Cold, credential-excluding audit copies. Never imports or starts restored apps."""
import pathlib,os,sys,time,json,sqlite3,hashlib,re,shutil,ast,plistlib
H=pathlib.Path.home(); host=sys.argv[1]; stamp=sys.argv[2]
root=H/'backups'/('agentic-baseline-'+stamp);root.mkdir(parents=True,exist_ok=False);os.chmod(root,0o700)
manifest={'host':host,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'root':str(root),'scope':'selected operational source and data only; no credentials, counselor stores, mailbox stores, Syncthing or Level8','files':[],'excluded':[],'restore_tests':[]}
patterns=[r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',r'\bsk-[A-Za-z0-9_-]{20,}',r'\b[0-9]{7,}:[A-Za-z0-9_-]{30,}',r'\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}',r'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.',r'(?i)(?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|approval[_-]?code|auth[_-]?token|bearer)[\w]*[\"\x27]?\s*[:=]\s*[\"\x27][^\"\x27\r\n]{6,}[\"\x27]']
def suspect(value):return isinstance(value,str) and any(re.search(x,value) for x in patterns)
def record(p,source,kind,extra=None):
 row={'path':str(p.relative_to(root)),'source':str(source),'kind':kind,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};row.update(extra or {});manifest['files'].append(row)
def copyfile(source):
 p=pathlib.Path(source)
 if not p.is_file() or p.is_symlink():manifest['excluded'].append({'path':str(p),'reason':'missing or symlink'});return
 raw=p.read_bytes()
 try:text=raw.decode('utf8')
 except UnicodeError:manifest['excluded'].append({'path':str(p),'reason':'non-text source excluded'});return
 if suspect(text):manifest['excluded'].append({'path':str(p),'reason':'credential-pattern guard; not copied'});return
 if p.suffix=='.plist':
  j=plistlib.loads(raw)
  if j.get('EnvironmentVariables') or any('--token' in str(a) for a in j.get('ProgramArguments',[])):
   manifest['excluded'].append({'path':str(p),'reason':'environment-bearing definition excluded; inventory preserves safe fields'});return
 dst=root/'files'/str(p).lstrip('/');dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);os.chmod(dst,0o600);record(dst,p,'exact-source')
def backupdb(source,allow=None):
 source=pathlib.Path(source)
 c=sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True);c.execute('pragma query_only=ON');c.execute('begin')
 tables=[r[0] for r in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")]
 if allow is not None:tables=[t for t in tables if t in allow]
 # Scan the same read transaction before writing any values to disk.
 for t in tables:
  for row in c.execute('select * from "'+t+'"'):
   if any(suspect(v) for v in row):
    manifest['excluded'].append({'path':str(source),'reason':'credential-pattern guard in selected data; no copy created'});c.rollback();c.close();return
 dst=root/'data'/source.name;dst.parent.mkdir(exist_ok=True);d=sqlite3.connect(dst)
 if allow is None:
  # Use the same pinned read transaction that passed the scan, including WAL state.
  c.backup(d)
 else:
  for t in tables:
   sql=c.execute("select sql from sqlite_master where type='table' and name=?",(t,)).fetchone()[0];d.execute(sql)
   for row in c.execute('select * from "'+t+'"'):d.execute('insert into "'+t+'" values ('+','.join('?' for _ in row)+')',tuple(row))
  d.commit()
 integrity=d.execute('pragma integrity_check').fetchone()[0];counts={t:d.execute('select count(*) from "'+t+'"').fetchone()[0] for t in tables}
 d.close();c.close();os.chmod(dst,0o600)
 record(dst,source,'consistent-sqlite' if allow is None else 'selected-table-export',{'integrity':integrity,'counts':counts})
if host=='HERALD-SUPPLEMENT':
 for rel in ['services/herald-staff-mcp/herald_staff_mcp.py','services/staff-records-mcp/staff_records_mcp.py','bin/windance_report_send.py','bin/windance_shawn_report_send.py','bin/telegram_report_history.py']:
  copyfile(H/rel)
elif host=='SAL-SUPPLEMENT':
 for rel in ['bin/send_report_payload.py','bin/send_shawn_email_payload.py','bin/send_shawn_report_payload.py','bin/send_telegram_payload.py','bin/send_william_imessage_payload.py','bin/send_william_sms_payload.py','bin/report_preferences.py','bin/sal_report_adapter.py','bin/windance_report_outcome.py','bin/windance_morning_status_report.py']:
  copyfile(H/rel)
elif host=='HERALD':
 for rel in ['services/vega-manager/manager.py','services/vega-manager/manager_mcp.py','services/vega-manager/MANAGER.md','services/agent-harness/agent_harness.py','services/windance-codex-bridge/server.mjs','services/herald-phone/phone_service.py','services/herald-phone/worker.py','services/herald-staff-mcp/server.py','services/google-workspace-mcp/google_workspace_mcp.py','services/staff-records-mcp/server.py','services/windance-gmail-mcp/server.py']:
  copyfile(H/rel)
 for folder in ['services/profile-staff-runner','services/windance-supervisor']:
  for p in (H/folder).glob('*.py'):copyfile(p)
 for role in ['herald','forge','sentinel','max','iris','ledger','scout','archivist','athena']:
  copyfile(H/'.hermes/profiles'/role/'SOUL.md')
 # Manager contains phone/user requests; exclude full messages/state, keeping operational recovery.
 backupdb(H/'.local/share/vega-manager/manager.db',['projects','stages','events'])
 backupdb(H/'.local/share/agent-harness/harness.db',['staff_tasks','staff_task_notes','staff_task_deliveries','staff_task_runs','staff_task_revisions','report_reviews'])
elif host=='SAL':
 for rel in ['bin/imessage_herald_bridge.py','bin/imessage_outbox_daemon.py','bin/send_imessage_payload.py','bin/windance_report_send.py','bin/windance_youtube_briefing.py','bin/windance_morning_news_briefing.py','bin/ledger_unpaid_invoice_report.py','bin/sam_training_completion_report.py','bin/windance_weekly_stack_review.py','.node-red/flows.json','.node-red/package.json','bin/start-node-red.sh']:
  copyfile(H/rel)
 for p in (H/'services/windance-supervisor').glob('*.py'):copyfile(p)
 backupdb(H/'services/windance-supervisor/incidents.sqlite')
elif host=='SAM-WIFI':
 for rel in ['services/sam-schedule/sam_schedule.py','bin/sam-schedule-kiosk.sh']:copyfile(H/rel)
 for p in pathlib.Path('/etc/systemd/system').glob('sam-schedule*'):copyfile(p)
 backupdb(H/'.local/share/sam-schedule/sam_schedule.db')
if host in ['HERALD','SAL']:
 for p in (H/'Library/LaunchAgents').glob('*.plist'):
  if any(x in p.name for x in ['windance','hermes','nodered']) and not any(x in p.name for x in ['jim','sandbox','level8']):copyfile(p)
# Selected restoration: fresh cold directory, exact readback, SQLite integrity+counts, syntax only.
restore=root/'isolation-restore';restore.mkdir();os.chmod(restore,0o700)
for entry in manifest['files']:
 src=root/entry['path'];dst=restore/entry['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);os.chmod(dst,0o600)
 ok=hashlib.sha256(dst.read_bytes()).hexdigest()==entry['sha256'];test={'path':entry['path'],'hash_match':ok}
 if entry['kind'] in ['consistent-sqlite','selected-table-export']:
  c=sqlite3.connect('file:'+str(dst)+'?mode=ro&immutable=1',uri=True);test['integrity']=c.execute('pragma integrity_check').fetchone()[0]
  test['row_counts_match']=all(c.execute('select count(*) from "'+t+'"').fetchone()[0]==n for t,n in entry['counts'].items());c.close()
 elif dst.suffix=='.py':
  try:ast.parse(dst.read_text());test['python_parse']='pass'
  except Exception as e:test['python_parse']=type(e).__name__
 elif dst.suffix=='.json':
  try:json.loads(dst.read_text());test['json_parse']='pass'
  except Exception as e:test['json_parse']=type(e).__name__
 elif dst.suffix=='.plist':
  try:plistlib.loads(dst.read_bytes());test['plist_parse']='pass'
  except Exception as e:test['plist_parse']=type(e).__name__
 manifest['restore_tests'].append(test)
manifest['isolation']={'services_started':0,'schedules_loaded':0,'task_dispatches':0,'network_calls_by_restore':0,'application_imports':0,'method':'offline byte/SQLite/parser restoration; files never installed in a live service directory'}
manifest['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));os.chmod(root/'MANIFEST.json',0o600)
print(json.dumps(manifest,indent=2))
