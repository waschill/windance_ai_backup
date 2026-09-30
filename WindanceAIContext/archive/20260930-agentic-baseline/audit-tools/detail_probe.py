import pathlib,json,sqlite3,time,re,sys,collections,urllib.request,subprocess,hashlib
H=pathlib.Path.home();host=sys.argv[1];out={'host':host,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
def readjson(p):
 try:return json.loads(p.read_text())
 except Exception:return {}
def safe(j):
 if isinstance(j,dict):return {k:safe(v) for k,v in j.items() if k in ['at','time','timestamp','date','job','status','ok','exit','exit_code','returncode','transport','service','configured','active_call','enabled','schedule','last_run','next_run','last_status','last_error','id','paused','runs','run_count','failures','error_count','started','finished','duration_seconds','sent','delivered','receipt','result','chunks'] and k not in ['last_error']}
 if isinstance(j,list):return [safe(x) for x in j]
 if isinstance(j,(bool,int,float)) or j is None:return j
 if isinstance(j,str) and not re.search(r'@|\+\d{9}|sk-|token|password',j,re.I):return j[:150]
 return '[omitted]'
if host=='HERALD':
 out['usage_7d']=[];out['cron']=[];cut=time.time()-604800
 for role in ['herald','forge','sentinel','max','iris','ledger','scout','archivist','athena']:
  p=H/'.hermes/profiles'/role/'state.db';c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
  q='select model,billing_provider,billing_mode,cost_status,count(*) sessions,sum(api_call_count) api_calls,sum(input_tokens) input_tokens,sum(output_tokens) output_tokens,sum(cache_read_tokens) cache_read_tokens,sum(estimated_cost_usd) estimated_cost_usd,sum(actual_cost_usd) actual_cost_usd,count(actual_cost_usd) actual_cost_rows from sessions where started_at>=? group by model,billing_provider,billing_mode,cost_status'
  try:out['usage_7d'].extend(dict(role=role,**dict(r)) for r in c.execute(q,(cut,)))
  except Exception as e:out['usage_7d'].append({'role':role,'error':type(e).__name__})
  c.close();p=H/'.hermes/profiles'/role/'cron/jobs.json'
  if p.exists():
   j=readjson(p); seq=j.get('jobs',[]) if isinstance(j,dict) else j
   out['cron'].append({'role':role,'top_keys':list(j) if isinstance(j,dict) else [],'jobs':[safe(x) for x in seq] if isinstance(seq,list) else 'mapping'})
 for name,url in [('phone','http://192.168.36.21:8796/health'),('bridge','http://127.0.0.1:8793/health')]:
  try:out[name]=safe(json.load(urllib.request.urlopen(url,timeout=8)))
  except Exception as e:out[name]={'error':type(e).__name__}
 p=H/'services/herald-phone/private/config.json';j=readjson(p);out['phone_config']={'enabled':j.get('enabled'),'config_exists':p.exists()}
 out['mcp_sources']={x:[p.name for p in (H/'services'/x).glob('*.py')] for x in ['herald-staff-mcp','staff-records-mcp']}
 paths=[]
 for base in ['services/capture-review-reminder','services/software-maintenance']:
  paths.extend((H/base).glob('*.log'))
else:
 out['outcomes']=[safe(json.loads(l)) for l in (H/'logs/windance-reports/nodered-outcomes.jsonl').read_text().splitlines()]
 out['youtube']=[safe(readjson(p)) for p in sorted((H/'.local/share/windance-supervisor/reports').glob('*.json')) if p.stat().st_mtime>time.time()-604800]
 out['shawn_delivery']=[safe(readjson(p)) for p in (H/'.local/share/shawn-email-delivery').glob('*.json')]
 counts=collections.Counter()
 for p in (H/'.local/share/windance-imessage-outbox/results').glob('*.json'):
  if p.stat().st_mtime>time.time()-604800:
   j=readjson(p);counts[str(j.get('ok'))]+=1
 out['outbox_result_7d']=dict(counts)
 paths=[H/'logs/ledger-unpaid-invoices.err.log',H/'logs/morning-news-briefing/morning-news-briefing.err.log',H/'logs/sam-training-completion-report.err.log',H/'logs/weekly-stack-review/weekly-stack-review.out.log']
out['log_diagnostics']=[]
for p in paths:
 if not p.exists():continue
 s=p.read_text(errors='replace')[-16000:]
 # Only fixed diagnostic signatures are exported, with counts and latest file time.
 needles=['receipt','SMS','iMessage','Traceback','Timeout','HTTP Error 502','HTTP Error 500','HTTP Error 403','HTTP Error 401','HTTP Error 400','HTTP Error 503','Connection refused','Telegram','backup','timed out','not approved','incomplete','sent','No report','PREPARE','FAILED','KeyError','AttributeError','not JSON serializable']
 out['log_diagnostics'].append({'path':str(p),'mtime':p.stat().st_mtime,'markers':{n:s.lower().count(n.lower()) for n in needles if n.lower() in s.lower()},'exception_types':re.findall(r'^([A-Za-z]+(?:Error|Exception)):',s,re.M)})
print(json.dumps(out,indent=2))
