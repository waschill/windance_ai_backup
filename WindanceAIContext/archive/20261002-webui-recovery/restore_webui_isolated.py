"""AL host: preserve private data backup; inspect a network-disabled cold clone."""
import hashlib,json,shutil,subprocess
from pathlib import Path

root=Path.home()/'backups/webui-recovery-20261002'
root.mkdir(mode=0o700,parents=True,exist_ok=False)
image='sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f'
summaries=[]
for container in ['open-webui','truth-engine-lab']:
    target=root/container;target.mkdir(mode=0o700)
    subprocess.run(['docker','cp',container+':/tmp/windance-webui-recovery-20261002/.',str(target)],check=True,capture_output=True)
    manifest=json.loads((target/'private-manifest.json').read_text())
    for name,expected in manifest['files'].items():
        assert hashlib.sha256((target/'data'/name).read_bytes()).hexdigest()==expected
    inspect=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
    assert inspect['Image']==image
    metadata={'image_id':image,'mounts':[{'type':m['Type'],'name':m.get('Name'),'destination':m['Destination']} for m in inspect['Mounts']],
              'ports':inspect['HostConfig']['PortBindings'],'limits':'Environment secrets intentionally not exported; full host rebuild not established'}
    (target/'deployment-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    cold=target/'cold-data';shutil.copytree(target/'data',cold)
    program="""import asyncio,json
from open_webui.models.users import Users
from open_webui.models.files import Files
async def main():
 print('WINDANCE_COLD_RESULT='+json.dumps({'users':await Users.get_num_users(),'files':await Files.count_files_by_user_id()}))
asyncio.run(main())
"""
    cmd=['docker','run','--rm','--pull=never','--network','none','--read-only','--tmpfs','/tmp',
         '--cpus','1','--memory','2g','--pids-limit','128','-e','OFFLINE_MODE=true','-e','HF_HUB_OFFLINE=1',
         '--mount',f'type=bind,src={cold},dst=/app/backend/data','--entrypoint','python',image,'-c',program]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
    (target/'cold-private.stdout').write_text(run.stdout);(target/'cold-private.stderr').write_text(run.stderr)
    lines=[line for line in run.stdout.splitlines() if line.startswith('WINDANCE_COLD_RESULT=')]
    result=json.loads(lines[-1].split('=',1)[1]) if lines else None
    expected=manifest['databases']['webui.db']
    passed=run.returncode==0 and result=={'users':expected['user']['count'],'files':expected['file']['count']}
    summaries.append({'container':container,'backup_hashes_verified':True,'cold_application_model_reads_passed':passed,
                      'cold_exit':run.returncode,'counts':result,'network':'none','published_ports':0,
                      'original_runtime_unchanged':True})
    for p in target.rglob('*'):
        if p.is_file():p.chmod(0o600)
        elif p.is_dir():p.chmod(0o700)
print(json.dumps({'backup_root':str(root),'results':summaries,'cache_excluded':True,'private_values_exported':False},indent=2))
assert all(r['cold_application_model_reads_passed'] for r in summaries),'Cold model read failed; inspect private logs without exporting contents'
