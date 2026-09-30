import pathlib,sqlite3,json,time,statistics,collections,re,sys,urllib.request
H=pathlib.Path.home(); host=sys.argv[1]; out={'host':host,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
def db(p):
 c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('pragma query_only=ON');return c
def rows(c,q,args=()):return [dict(r) for r in c.execute(q,args)]
def stats(v):
 v=sorted(v);return {'n':len(v),'p50_seconds':round(statistics.median(v),2),'p95_nearest_rank_seconds':round(v[max(0,__import__('math').ceil(.95*len(v))-1)],2),'max_seconds':round(max(v),2)} if v else {'n':0}
if host=='HERALD':
 c=db(H/'.local/share/vega-manager/manager.db')
 out['messages']=rows(c,'select channel,status,count(*) n from messages group by channel,status')
 out['latency']={ch:stats([r[0] for r in c.execute('select updated-created from messages where status=? and channel=?',('answered',ch))]) for ch, in c.execute('select distinct channel from messages')}
 out['receipts']={}
 for row in c.execute('select channel,status,notify,receipt from messages'):
  key=row['channel'];x=out['receipts'].setdefault(key,{'notify_rows':0,'successful_receipts':0,'missing_or_failed':0})
  if row['notify']:
   x['notify_rows']+=1
   try:ok=json.loads(row['receipt'] or '{}').get('ok') is True
   except Exception:ok=False
   x['successful_receipts' if ok else 'missing_or_failed']+=1
 out['projects']=rows(c,'select id,status,report_hash,owner from projects')
 out['stages']=rows(c,'select project,status,count(*) n from stages group by project,status');c.close()
 c=db(H/'.local/share/agent-harness/harness.db')
 out['staff_tasks']=rows(c,'select assignee,status,count(*) n from staff_tasks group by assignee,status')
 out['staff_window']=rows(c,'select min(created_at) first,max(updated_at) last,count(*) n from staff_tasks')
 out['staff_deliveries']=rows(c,'select transport,status,count(*) n from staff_task_deliveries group by transport,status')
 out['reports']=rows(c,'select kind,count(*) n,max(created_at) last from report_snapshots group by kind')
 out['reviews']=rows(c,'select reviewer,provider,model,approved,count(*) n,max(created_at) last from report_reviews group by reviewer,provider,model,approved');c.close()
 out['usage_schemas']={}
 for role in ['herald','forge','sentinel','max','iris','ledger','scout','archivist','athena']:
  p=H/'.hermes/profiles'/role/'state.db'
  try:
   c=db(p);out['usage_schemas'][role]={r[0]:[x[1] for x in c.execute('pragma table_info("'+r[0]+'")')] for r in c.execute("select name from sqlite_master where type='table'") if any(x in r[0] for x in ['session','usage'])};c.close()
  except Exception as e:out['usage_schemas'][role]={'error':type(e).__name__}
 out['cron']={}
 for role in ['herald','forge','sentinel','max','iris','ledger','scout','archivist','athena']:
  p=H/'.hermes/profiles'/role/'cron';out['cron'][role]=[str(x.relative_to(p)) for x in p.rglob('*') if x.is_file() and len(x.relative_to(p).parts)<3][:30]
else:
 c=db(H/'Library/Messages/chat.db')
 out['messages_7d']=rows(c,"select service,is_sent,is_delivered,count(*) n from message where is_from_me=1 and date > (strftime('%s','now')-978307200-604800)*1000000000 group by service,is_sent,is_delivered")
 out['selected_rows']=rows(c,"select ROWID,service,is_sent,is_delivered,datetime(date/1000000000+978307200,'unixepoch') at from message where ROWID in (3265,3274)");c.close()
 out['report_files']={}
 for folder in ['.local/share/windance-supervisor','.local/share/windance-reports','.local/share/shawn-email-delivery','.local/share/windance-imessage-outbox','logs/windance-reports','logs/youtube-briefing','logs/weekly-stack-review']:
  p=H/folder; files=sorted((x for x in p.rglob('*') if x.is_file()),key=lambda x:x.stat().st_mtime,reverse=True)[:8]
  out['report_files'][folder]=[{'path':str(x),'bytes':x.stat().st_size,'mtime':x.stat().st_mtime} for x in files]
# Read only error categories/counts, never return message bodies or credentials.
out['log_evidence']=[]
folders=[H/'logs',H/'services/capture-review-reminder',H/'services/software-maintenance'] if host=='HERALD' else [H/'logs']
for folder in folders:
 for p in folder.rglob('*'):
  if not p.is_file() or p.suffix not in ['.log','.jsonl'] or any(x in str(p).lower() for x in ['jim','jean','counsel','claude','kanak']):continue
  if p.stat().st_mtime<time.time()-7*86400:continue
  if p.stat().st_size>100000000:continue
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-100000));text=f.read().decode('utf8','replace')
  counts={w:len(re.findall(w,text,re.I)) for w in ['Traceback','TimeoutError','PermissionError','ConnectionRefusedError','HTTPError','RuntimeError','receipt','Traceback','delivered','failed','SMS','imessage']}
  out['log_evidence'].append({'path':str(p),'mtime':p.stat().st_mtime,'bytes':p.stat().st_size,'tail_bytes':min(100000,p.stat().st_size),'markers':{k:v for k,v in counts.items() if v}})
print(json.dumps(out,indent=2))
