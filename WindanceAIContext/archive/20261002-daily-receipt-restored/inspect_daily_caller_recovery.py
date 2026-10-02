import hashlib,json,os,plistlib,re,subprocess
from pathlib import Path
home=Path.home();records=[]
for label,folder,filename,journal in [('com.windance.capture-review-reminder','capture-review-reminder','capture_review_reminder.py','capture-report-delivery'),('com.windance.sentinel-router-review','sentinel-router-logs','sentinel_daily_router_review.py','sentinel-report-delivery')]:
 p=home/'Library/LaunchAgents'/(label+'.plist');d=plistlib.loads(p.read_bytes());states=[];disabled={}
 for domain in ('user','gui'):
  target=f'{domain}/{os.getuid()}'
  if subprocess.run(['launchctl','print',target+'/'+label],capture_output=True).returncode==0:states.append(domain)
  raw=subprocess.run(['launchctl','print-disabled',target],capture_output=True,text=True).stdout
  m=re.search(re.escape('"'+label+'"')+r'\s*=>\s*(true|false)',raw)
  disabled[domain]=m.group(1) if m else 'not_listed'
 source=home/'services'/folder/filename
 records.append({'label':label,'registered':states,'disabled_overrides':disabled,'calendar':d.get('StartCalendarInterval'),'run_at_load':d.get('RunAtLoad'),'session_type':d.get('LimitLoadToSessionType'),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'plist_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'journal_exists':(home/'.local/share'/journal/'reports.db').exists()})
print(json.dumps({'jobs':records,'timezone':subprocess.run(['date','+%Z'],capture_output=True,text=True).stdout.strip()}))
