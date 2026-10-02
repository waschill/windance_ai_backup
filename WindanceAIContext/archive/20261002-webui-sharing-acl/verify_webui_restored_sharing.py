"""AL: actual ASGI route checks on isolated copies; no lifecycle scheduler."""
import datetime,hashlib,json,os,shutil,subprocess
from pathlib import Path
os.umask(0o077)
source=Path.home()/'backups/webui-recovery-20261002'
root=Path.home()/'backups'/('webui-sharing-check-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
root.mkdir(mode=0o700)
program=Path(__file__).with_name('webui_sharing_probe.py').read_text()

results=[]
for instance in ('open-webui','truth-engine-lab'):
    old=source/instance;m=json.loads((old/'private-manifest.json').read_text())
    assert all(hashlib.sha256((old/'data'/n).read_bytes()).hexdigest()==h for n,h in m['files'].items())
    target=root/instance;shutil.copytree(old/'data',target)
    image=json.loads((old/'deployment-metadata.json').read_text())['image_id']
    assert image=='sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f'
    name='windance-webui-sharing-'+instance+'-'+root.name.rsplit('-',1)[1].lower()
    cmd=['docker','run','--name',name,'--rm','--pull=never','--network','none','--read-only','--tmpfs','/tmp','--cpus','1','--memory','2g','--pids-limit','128',
         '-e','OFFLINE_MODE=true','-e','HF_HUB_OFFLINE=1','--mount',f'type=bind,src={target},dst=/app/backend/data','--entrypoint','python',image,'-c',program]
    try:
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (root/(instance+'.private.stdout')).write_text(run.stdout)
        (root/(instance+'.private.stderr')).write_text(run.stderr)
        lines=[s for s in run.stdout.splitlines() if s.startswith('WINDANCE_RESULT=')]
        result=json.loads(lines[-1].split('=',1)[1]) if lines else {'passed':False,'no_result':True}
        result.update(instance=instance,exit=run.returncode)
    except subprocess.TimeoutExpired:
        result={'instance':instance,'passed':False,'timeout':True}
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
        remaining=subprocess.run(['docker','inspect',name],capture_output=True,timeout=15)
        assert remaining.returncode!=0,'Test container cleanup not confirmed'
    assert all(hashlib.sha256((old/'data'/n).read_bytes()).hexdigest()==h for n,h in m['files'].items())
    results.append(result)
print(json.dumps({'results':results,'backup_source_unchanged':True,'test_containers_removed':True,'private_test_root':str(root),'production_changes':False,
 'limits':'Saved snapshot, ephemeral signing key, no lifespan/startup schedulers. Synthetic users and test-signed sessions only; original login, knowledge behavior and full service startup unverified.'}))



