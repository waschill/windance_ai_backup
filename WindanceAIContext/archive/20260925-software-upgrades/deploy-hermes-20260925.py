import pathlib, subprocess, json, hashlib, os, plistlib, re, shutil, sqlite3
os.umask(0o077)
home=pathlib.Path('/Users/herald')
root=home/'.hermes/hermes-agent'
recovery=home/'services/maintenance-recovery-20260925'
candidate=recovery/'hermes-candidate'
def run(args,**kw): return subprocess.run(args,check=True,text=True,**kw)
def out(args): return subprocess.check_output(args,text=True)
def fingerprints():
    paths=list((home/'.hermes').glob('config.yaml'))+list((home/'.hermes/profiles').glob('*/config.yaml'))+list((home/'.hermes/profiles').glob('*/SOUL.md'))
    for base in [home/'.hermes/plugins',home/'.hermes/profiles/herald/plugins']:
        paths.extend(p for p in base.rglob('*') if p.is_file() and p.suffix in ('.py','.yaml','.json','.js','.md') and '__pycache__' not in p.parts)
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=fingerprints()
(recovery/'protected-config-hashes.json').write_text(json.dumps(before,indent=2))
db=home/'.local/share/agent-harness/harness.db'
with sqlite3.connect(str(db)) as c:
    active=c.execute("select count(*) from staff_tasks where status in ('running','dispatching')").fetchone()[0]
    assert active==0, f'{active} active staff tasks; do not interrupt'
    with sqlite3.connect(str(recovery/'harness-before.db')) as dest:c.backup(dest)
print('NO_ACTIVE_STAFF_TASKS; DATABASE_BACKUP_READY',flush=True)
for state in [home/'.hermes/state.db',*(home/'.hermes/profiles').glob('*/state.db')]:
    if state.is_file():
        label='default' if state.parent==home/'.hermes' else state.parent.name
        with sqlite3.connect(str(state)) as source:
            with sqlite3.connect(str(recovery/('state-'+label+'.before.db'))) as dest:source.backup(dest)
def packages(py):
    return json.loads(out([str(py),'-c','import importlib.metadata,json; print(json.dumps({d.metadata["Name"].lower():d.version for d in importlib.metadata.distributions()}))']))
old=packages(root/'venv/bin/python');new=packages(candidate/'venv/bin/python')
changes={k:(old.get(k),v) for k,v in new.items() if old.get(k)!=v}
assert set(changes)<= {'hermes-agent'}, changes
assert out(['git','-C',str(root),'rev-parse','HEAD']).strip().startswith('b9271bcb34')
assert (candidate/'hermes_cli/web_dist/index.html').is_file()
assert (recovery/'hermes-agent.before/hermes_cli/web_dist/index.html').is_file()
jobs=[]
for p in (home/'Library/LaunchAgents').glob('*.plist'):
    d=plistlib.load(p.open('rb'));args=d.get('ProgramArguments',[])
    if not any('hermes-agent' in x or '/.local/bin/hermes' in x for x in args):continue
    label=d['Label']; r=subprocess.run(['launchctl','print',f'gui/{os.getuid()}/{label}'],capture_output=True,text=True)
    if r.returncode==0 and re.search(r'\bpid = [1-9]',r.stdout):jobs.append((label,str(p)))
(recovery/'restarted-jobs.json').write_text(json.dumps(jobs,indent=2))
print('RESTARTING_JOBS',','.join(x[0] for x in jobs),flush=True)
stopped=[]
try:
    for label,p in jobs:
        run(['launchctl','bootout',f'gui/{os.getuid()}/{label}']);stopped.append((label,p))
    with (recovery/'production-install.log').open('w') as log:
        run(['git','-C',str(root),'merge','--ff-only','v2026.9.24'],stdout=log,stderr=subprocess.STDOUT)
        run([str(root/'venv/bin/python'),'-m','pip','install','--no-deps','-e',str(root)],stdout=log,stderr=subprocess.STDOUT)
    shutil.copytree(candidate/'hermes_cli/web_dist',root/'hermes_cli/web_dist',dirs_exist_ok=True)
    for sub in ['node_modules','web/node_modules','ui-tui/node_modules','ui-tui/dist']:
        source=candidate/sub
        if not source.exists():continue
        target=root/sub
        if target.exists():
            backup=recovery/('production-'+sub.replace('/','-')+'.before')
            assert not backup.exists()
            target.rename(backup)
        shutil.copytree(source,target,symlinks=True)
    assert fingerprints()==before, 'Protected configuration changed'
    run([str(root/'venv/bin/python'),'-c','import hermes_cli.main,run_agent,model_tools,toolsets; print("PRODUCTION_IMPORTS_PASS")'],cwd=root)
    print('HERMES_DEPLOYED',out(['git','-C',str(root),'rev-parse','HEAD']).strip(),flush=True)
finally:
    for label,p in reversed(stopped):
        r=subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',p],capture_output=True,text=True)
        print('SERVICE_RELOAD',label,r.returncode,flush=True)
        if r.returncode: print(r.stderr[:300])
