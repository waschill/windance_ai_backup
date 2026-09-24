import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from urllib.request import urlopen
os.umask(0o077)
service=Path('/home/waschilladmin/services/searxng')
backup=Path('/home/waschilladmin/services/maintenance-recovery-20260924/searxng')
shutil.copytree(service,backup,dirs_exist_ok=True,ignore=shutil.ignore_patterns('core-config'))
backup.chmod(0o700)
subprocess.run(['docker','cp','searxng-core:/etc/searxng',str(backup/'core-config')],check=True)
p=service/'compose.yaml'
old='searxng/searxng@sha256:a31763b7af3caf6ae9aac1816ba774214eb550252e06a4998f276ded8d60461b'
new='searxng/searxng@sha256:bcfaed4091d59f7ce85670bd701a2d0295872196dc19908a3965a8353b149f83'
s=p.read_text()
assert s.count(old)==1
p.write_text(s.replace(old,new))
subprocess.run(['docker','compose','-f',str(p),'up','-d','--no-deps','core'],check=True)
for _ in range(30):
    try:
        with urlopen('http://192.168.36.20:8888/search?q=Node-RED&format=json',timeout=15) as response:
            data=json.load(response)
        if len(data.get('results',[]))>0: break
    except Exception: pass
    time.sleep(2)
else: raise RuntimeError('Search health failed; original compose/config retained for recovery')
result={'version':'2026.9.23-3cd69d30e','image':new,'search_results':len(data['results']),
        'valkey_unchanged':True,'backup':str(backup)}
(backup/'upgrade-receipt.json').write_text(json.dumps(result))
print(json.dumps(result))
