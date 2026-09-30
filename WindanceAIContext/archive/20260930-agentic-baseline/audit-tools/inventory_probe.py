import os,sys,json,time,pathlib,sqlite3,plistlib,subprocess,urllib.request,urllib.error,hashlib,platform,collections
P=pathlib.Path
host=sys.argv[1]
home=P.home()
out={'host':host,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'os':platform.platform()}
def run(args):
 try:
  r=subprocess.run(args,capture_output=True,text=True,timeout=15)
  return {'exit':r.returncode,'output':r.stdout.strip()[:18000]}
 except Exception as e:return {'error':type(e).__name__}
def health(url):
 t=time.monotonic()
 try:
  with urllib.request.urlopen(url,timeout=8) as r:
   raw=r.read(200000); result={'http':r.status,'ms':round((time.monotonic()-t)*1000,2)}
   try:
    j=json.loads(raw); result['fields']={k:v for k,v in j.items() if k in ['status','ok','service','configured','active_call','enabled','auth_required','version','tick_age_seconds','active_turns','queued_turns','projects','provider','model','fallback_enabled'] and isinstance(v,(str,int,float,bool,type(None),dict))}
   except Exception:pass
   return result
 except urllib.error.HTTPError as e:return {'http':e.code}
 except Exception as e:return {'error':type(e).__name__}
out['disk']=run(['df','-k','/'])
if host in ['HERALD','SAL']:
 jobs=[]
 for p in sorted((home/'Library/LaunchAgents').glob('*.plist')):
  try:
   j=plistlib.loads(p.read_bytes()); label=j.get('Label','')
   if not any(x in label.lower() for x in ['windance','hermes','node','cloudflare','shawn','codex']):continue
   row={k:j[k] for k in ['Label','Disabled','RunAtLoad','KeepAlive','StartInterval','StartCalendarInterval','LimitLoadToSessionType','WorkingDirectory','StandardOutPath','StandardErrorPath'] if k in j}
   row['file']=str(p); row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
   row['executables']=[x for x in j.get('ProgramArguments',[]) if isinstance(x,str) and x.startswith('/') and not any(t in x.lower() for t in ['secret','token','credential'])]
   row['domains']={}
   for domain in ['user','gui']:
    r=run(['launchctl','print',f'{domain}/{os.getuid()}/{label}'])
    if r.get('exit')==0:
     fields={}
     for line in r['output'].splitlines():
      a,_,b=line.strip().partition(' = ')
      if a in ['state','pid','runs','last exit code']:fields[a]=b
     row['domains'][domain]=fields
   jobs.append(row)
  except Exception as e:jobs.append({'file':str(p),'error':type(e).__name__})
 out['jobs']=jobs
if host=='HERALD':
 out['health']={str(port)+path:health(f'http://127.0.0.1:{port}{path}') for port,path in [(8791,'/health'),(8793,'/health'),(8795,'/health'),(8796,'/health'),(8797,'/health'),(9120,'/api/status'),(8791,'/odoo/status'),(8791,'/search/status')]}
 try:
  import yaml
  out['profiles']=[]
  for name in ['herald','forge','sentinel','max','iris','ledger','scout','archivist','athena']:
   p=home/'.hermes/profiles'/name/'config.yaml'; j=yaml.safe_load(p.read_text())
   model=j.get('model'); allowed={k:v for k,v in model.items() if k in ['default','provider','base_url']} if isinstance(model,dict) else model
   out['profiles'].append({'name':name,'model':allowed,'fallback_models':j.get('fallback_models'),'mcp_names':list(j.get('mcp_servers',{})),'config_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  j=yaml.safe_load((home/'.hermes/config.yaml').read_text());out['root_mcp_names']=list(j.get('mcp_servers',{}))
 except Exception as e:out['profile_error']=type(e).__name__
 out['hermes_git']=run(['git','-C',str(home/'.hermes/hermes-agent'),'rev-parse','HEAD'])
 out['hermes_version']=run([str(home/'.local/bin/hermes'),'--version'])
 dbs=[home/'.local/share/vega-manager/manager.db',home/'.local/share/agent-harness/harness.db']
elif host=='SAL':
 out['health']={'nodered':health('http://127.0.0.1:1880/')}
 dbs=[home/'services/windance-supervisor/incidents.sqlite']
 p=home/'.node-red/flows.json'
 if p.exists():
  nodes=json.loads(p.read_text());out['nodered']={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'node_count':len(nodes),'types':dict(collections.Counter(n.get('type') for n in nodes)),'schedules':[ {k:n[k] for k in ['id','type','name','z','disabled','d','repeat','crontab','once','onceDelay'] if k in n} for n in nodes if n.get('type') in ['inject','cronplus','bigtimer','tab']]}
elif host=='SAM-WIFI':
 out['health']={'sam':health('http://127.0.0.1:8088/api/health')}
 out['timers']=run(['systemctl','list-timers','--all','--no-pager'])
 p=home/'services/sam-schedule/sam_schedule.py';s=p.read_text()
 out['source']={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'suspension_lines':[l.strip() for l in s.splitlines() if 'suspend' in l.lower() or '410' in l][:15]}
 dbs=[home/'.local/share/sam-schedule/sam_schedule.db']
else:dbs=[]
out['databases']=[]
for p in dbs:
 try:
  c=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True); c.execute('PRAGMA query_only=ON')
  tables={r[0]:[x[1] for x in c.execute('pragma table_info("'+r[0]+'")')] for r in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")}
  out['databases'].append({'path':str(p),'bytes':p.stat().st_size,'schema':tables});c.close()
 except Exception as e:out['databases'].append({'path':str(p),'error':type(e).__name__})
print(json.dumps(out,indent=2))
