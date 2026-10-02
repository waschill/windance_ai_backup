"""Create and verify an unstarted replacement; credentials stay in Docker/in memory."""
import copy,hashlib,http.client,json,socket,subprocess
from pathlib import Path
class Docker(http.client.HTTPConnection):
    def __init__(self):super().__init__('localhost',timeout=15)
    def connect(self):self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.connect('/var/run/docker.sock')
def api(method,path,body=None):
    connection=Docker();connection.request(method,'/v1.56'+path,body=json.dumps(body) if body is not None else None,headers={'Content-Type':'application/json'})
    response=connection.getresponse();raw=response.read();connection.close()
    if response.status>=300:raise RuntimeError('Docker API failed with status '+str(response.status))
    return json.loads(raw) if raw else None
def inspect(name):return api('GET','/containers/'+name+'/json')
original=inspect('truth-engine-lab')
assert original['Id']=='ece8e5dcacd21a307cf17295db9d67cb1406ce94d8732af568511c120e078fbb'
assert original['State']['Running'] and original['HostConfig']['NetworkMode']=='bridge'
assert original['Image']=='sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f'
assert set(original['NetworkSettings']['Networks'])=={'bridge'}
config=copy.deepcopy(original['Config']);config['Image']=original['Image']
updates={'ENABLE_INITIAL_ADMIN_SIGNUP':'false','ENABLE_SIGNUP':'false','ENABLE_LOGIN_FORM':'false'}
env=dict(value.split('=',1) for value in config['Env']);env.update(updates)
config['Env']=[key+'='+value for key,value in env.items()]
payload={**config,'HostConfig':copy.deepcopy(original['HostConfig'])}
name='truth-engine-lab-containment-staged-20261002'
new_id=api('POST','/containers/create?name='+name,payload)['Id']
try:
    staged=inspect(new_id)
    assert staged['State']['Status']=='created' and not staged['State']['Running']
    assert staged['Image']==original['Image']
    host_differences=[key for key in set(staged['HostConfig'])|set(original['HostConfig']) if staged['HostConfig'].get(key)!=original['HostConfig'].get(key)]
    normalized_oom=False
    if host_differences==['OomKillDisable'] and original['HostConfig']['OomKillDisable'] in (None,False) and staged['HostConfig']['OomKillDisable'] in (None,False):
        normalized_oom=True
    else:assert not host_differences,'Host configuration differs'
    differences=[key for key in set(config)|set(staged['Config']) if config.get(key)!=staged['Config'].get(key)]
    assert differences==[], 'Docker normalized unexpected Config fields'
    assert [(m['Type'],m.get('Name'),m['Destination'],m['RW']) for m in staged['Mounts']]==[(m['Type'],m.get('Name'),m['Destination'],m['RW']) for m in original['Mounts']]
    assert inspect(original['Id'])['State']['Running']
except Exception:
    api('DELETE','/containers/'+new_id);raise
record={'original_id':original['Id'],'staged_id':new_id,'staged_name':name,'staged_started':False,'image_id':original['Image'],'host_config_match_except_oom_false_null_normalization':True,'oom_false_null_normalized':normalized_oom,'mounts_exact_match':True,'unrelated_config_exact_match':True,'changed_environment_names':sorted(updates),'original_running':True}
destination=Path('/home/waschilladmin/backups/webui-lab-precontainment-20261002T1816/container-transition.json')
with destination.open('x') as stream:json.dump(record,stream,indent=2)
print(json.dumps(record))
