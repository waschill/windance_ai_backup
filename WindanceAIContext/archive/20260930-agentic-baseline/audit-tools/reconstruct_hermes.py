import pathlib,subprocess,os,json,hashlib,time
root=pathlib.Path.home()/'backups/agentic-baseline-20260930T0600Z/hermes-reconstruction'
root.mkdir(exist_ok=False);os.chmod(root,0o700)
repo=pathlib.Path.home()/'.hermes/hermes-agent';env=dict(os.environ,GIT_INDEX_FILE=str(root/'isolated.index'))
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],env=env)
head=git('rev-parse','HEAD').decode().strip();git('read-tree',head)
patch=pathlib.Path('/tmp/baseline-hermes.patch');git('apply','--cached','--check',str(patch));git('apply','--cached',str(patch))
names=git('diff','--cached','--name-only',head).decode().splitlines();results=[]
for name in names:
 data=git('show',':'+name);live=(repo/name).read_bytes();p=root/'restored'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 results.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'matches_live':data==live})
guard=pathlib.Path('/tmp/baseline-owner-guard.py').read_bytes();p=root/'restored/gateway/windance_owner_guard.py';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(guard)
results.append({'path':'gateway/windance_owner_guard.py','sha256':hashlib.sha256(guard).hexdigest(),'matches_live':guard==(repo/'gateway/windance_owner_guard.py').read_bytes()})
out={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'base':head,'root':str(root),'patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'files':results,'isolated_index':True,'live_worktree_modified':False,'applications_started':0}
(root/'VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
