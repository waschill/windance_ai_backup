"""Retry existing cold clones with an ephemeral, unexported test signing key."""
import json,subprocess
from pathlib import Path
root=Path.home()/'backups/webui-recovery-20261002';results=[]
program="""import os,secrets,asyncio,json
os.environ['WEBUI_SECRET_KEY']=secrets.token_urlsafe(48)
from open_webui.models.users import Users
from open_webui.models.files import Files
async def main():
 print('WINDANCE_COLD_RESULT='+json.dumps({'users':await Users.get_num_users(),'files':await Files.count_files_by_user_id()}))
asyncio.run(main())
"""
for container in ['open-webui','truth-engine-lab']:
    target=root/container;cold=target/'cold-data';manifest=json.loads((target/'private-manifest.json').read_text())
    image=json.loads((target/'deployment-metadata.json').read_text())['image_id']
    cmd=['docker','run','--rm','--pull=never','--network','none','--read-only','--tmpfs','/tmp','--cpus','1','--memory','2g','--pids-limit','128',
      '-e','OFFLINE_MODE=true','-e','HF_HUB_OFFLINE=1','--mount',f'type=bind,src={cold},dst=/app/backend/data','--entrypoint','python',image,'-c',program]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
    for suffix,value in [('stdout',run.stdout),('stderr',run.stderr)]:
        p=target/('cold-r2-private.'+suffix);p.write_text(value);p.chmod(0o600)
    lines=[x for x in run.stdout.splitlines() if x.startswith('WINDANCE_COLD_RESULT=')]
    counts=json.loads(lines[-1].split('=',1)[1]) if lines else None
    expected=manifest['databases']['webui.db']
    passed=run.returncode==0 and counts=={'users':expected['user']['count'],'files':expected['file']['count']}
    results.append({'container':container,'exit':run.returncode,'cold_model_reads_passed':passed,'counts':counts,
                    'network':'none','production_secret_used':False,'ephemeral_test_key_persisted':False})
print(json.dumps({'results':results,'production_changed':False,'private_values_exported':False},indent=2))
assert all(r['cold_model_reads_passed'] for r in results)
