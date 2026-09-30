import pathlib,json,sqlite3,time,sys,re,plistlib,urllib.request,hashlib
H=pathlib.Path.home();out={};host=sys.argv[1]
def error_types(p):
 if not p.exists():return {'exists':False}
 s=p.read_text(errors='replace')[-20000:];lines=[]
 for l in s.splitlines():
  if re.match(r'^(?:\w*Error|\w*Exception):',l):
   # Only exception headline; strip payload and any contact-like text.
   l=re.split(r'[\[{]',l,maxsplit=1)[0][:200]
   l=re.sub(r'\b[\w.+-]+@[\w.-]+\b|\+?\d[\d ()-]{8,}\d','[private]',l)
   if not re.search('token|password|api.?key|bearer|authorization',l,re.I):lines.append(l)
 return {'mtime':p.stat().st_mtime,'exception_headlines':lines[-5:]}
if host=='HERALD':
 import yaml
 out['profiles']={}
 for role in ['herald','forge','sentinel','max','iris','ledger','scout','archivist','athena']:
  j=yaml.safe_load((H/'.hermes/profiles'/role/'config.yaml').read_text());out['profiles'][role]={k:v for k,v in j.items() if 'fallback' in k.lower()}
  p=H/'.hermes/profiles'/role/'cron/jobs.json'
  if p.exists():
   jobs=json.loads(p.read_text()).get('jobs',[])
   out.setdefault('native_jobs',[]).extend({'role':role,'id':x.get('id'),'enabled':x.get('enabled'),'schedule':x.get('schedule'),'last_status':x.get('last_status'),'next_run_at':x.get('next_run_at'),'last_run_at':x.get('last_run_at'),'error_class':('notebook/tool configuration' if 'config' in str(x.get('last_status')) else 'error recorded' if x.get('last_status')=='error' else None)} for x in jobs)
 out['errors']={n:error_types(H/'logs'/n) for n in ['capture-review-reminder.err.log','software-maintenance.err.log','software-maintenance.log','capture-review-reminder.log']}
 out['bridge_model_source']={}
 s=(H/'services/windance-codex-bridge/server.mjs').read_text()
 out['bridge_model_source']['model_literals']=sorted(set(re.findall(r'gpt-[a-zA-Z0-9.\-]+',s)))
 j=plistlib.loads((H/'Library/LaunchAgents/com.windance.codex-bridge.plist').read_bytes());out['bridge_model_env']={k:v for k,v in j.get('EnvironmentVariables',{}).items() if k in ['CODEX_MODEL','CODEX_REASONING_EFFORT','CODEX_APPROVAL_POLICY','CODEX_SANDBOX']}
 out['integration_fields']={}
 for path in ['/odoo/status','/search/status']:
  j=json.load(urllib.request.urlopen('http://127.0.0.1:8791'+path,timeout=15));out['integration_fields'][path]={k:v for k,v in j.items() if isinstance(v,(bool,int)) and not any(x in k.lower() for x in ['uid','user','key','token'])};out['integration_fields'][path]['field_names']=list(j)
else:
 out['errors']={n:error_types(H/'logs'/n) for n in ['morning-news-briefing/morning-news-briefing.err.log','sam-training-completion-report.err.log','ledger-unpaid-invoices.log']}
 out['outcomes']=[]
 for l in (H/'logs/windance-reports/nodered-outcomes.jsonl').read_text().splitlines():
  j=json.loads(l);out['outcomes'].append({k:v for k,v in j.items() if k in ['job','status','exit_code','ts','at','date','local_date','recorded_at','correlation']})
 out['youtube']=[]
 for p in (H/'.local/share/windance-supervisor/reports').glob('*.json'):
  j=json.loads(p.read_text());out['youtube'].append({k:v for k,v in j.items() if k not in ['stdout','stderr','recipient','body','text','command','args']})
 # Correlate known canary by its task ID in memory, return only delivery metadata.
 c=sqlite3.connect('file:'+str(H/'Library/Messages/chat.db')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
 out['known_transport_rows']=[dict(r) for r in c.execute("select ROWID,is_from_me,service,is_sent,is_delivered,datetime(date/1000000000+978307200,'unixepoch') at from message where ROWID in (3265,3274,3275,3276)")];c.close()
print(json.dumps(out,indent=2))
