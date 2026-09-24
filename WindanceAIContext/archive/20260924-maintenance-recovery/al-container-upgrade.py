import copy, http.client, json, os, socket, subprocess, sys, time
from pathlib import Path

TARGETS = {
    'truth-engine-lab': ('ghcr.io/open-webui/open-webui:v0.11.4','/app/backend/data','http://192.168.36.20:3001/api/version','0.11.4'),
    'open-webui': ('ghcr.io/open-webui/open-webui:v0.11.4','/app/backend/data','http://127.0.0.1:3000/api/version','0.11.4'),
    'portainer': ('portainer/portainer-ce:2.45.1','/data','https://127.0.0.1:9443/api/status','2.45.1'),
}
class DockerConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(120)
        self.sock.connect('/var/run/docker.sock')
def api(method, path, body=None):
    c=DockerConnection('localhost',timeout=120)
    c.request(method,'/v1.45'+path,body=json.dumps(body) if body is not None else None,
              headers={'Content-Type':'application/json'})
    r=c.getresponse(); data=r.read(); status=r.status; c.close()
    if status>=400: raise RuntimeError('Docker operation failed: '+method+' '+path+' HTTP '+str(status))
    return json.loads(data) if data else None
def command(*args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode: raise RuntimeError('Command failed: '+args[0]+' '+args[1])
    return p.stdout

def main(name):
    if name not in TARGETS: raise ValueError('Target not allowed')
    os.umask(0o077)
    image,data_path,url,version=TARGETS[name]
    root=Path.home()/'services'/'maintenance-recovery-20260924'/name
    root.mkdir(parents=True,exist_ok=False)
    old=api('GET','/containers/'+name+'/json')
    if old['HostConfig']['NetworkMode']!='bridge': raise RuntimeError('Unexpected network mode')
    (root/'container-before.private.json').write_text(json.dumps(old))
    command('docker','pull',image)
    target=json.loads(command('docker','image','inspect',image))[0]['Id']
    archived=name+'-before-20260924'
    api('POST','/containers/'+name+'/stop?t=30')
    try:
        command('docker','cp',name+':'+data_path,str(root/'data-before'))
    except Exception:
        api('POST','/containers/'+name+'/start'); raise
    api('POST','/containers/'+name+'/update',{'RestartPolicy':{'Name':'no'}})
    api('POST','/containers/'+name+'/rename?name='+archived)
    config=copy.deepcopy(old['Config'])
    config['Image']=target
    config['HostConfig']=copy.deepcopy(old['HostConfig'])
    # Named Binds preserve the exact existing data volumes and socket binding.
    if not config['HostConfig'].get('Binds'): raise RuntimeError('Missing explicit existing binds')
    new=api('POST','/containers/create?name='+name,config)
    api('POST','/containers/'+new['Id']+'/start')
    for _ in range(90):
        try:
            response=json.loads(command('curl','-kfsS','--max-time','5',url))
            actual=response.get('version',response.get('Version'))
            if actual==version: break
        except Exception: pass
        time.sleep(2)
    else:
        raise RuntimeError('Version health check failed; retain old container and private data snapshot for manual rollback')
    current=api('GET','/containers/'+name+'/json')
    assert current['HostConfig']['Binds']==old['HostConfig']['Binds']
    assert current['HostConfig']['PortBindings']==old['HostConfig']['PortBindings']
    assert current['Config']['Env']==old['Config']['Env']
    receipt={'name':name,'version':actual,'image':target,'old_container':archived,
             'bindings_preserved':True,'environment_preserved':True,'health_url':url}
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt))

if __name__=='__main__': main(sys.argv[1])
