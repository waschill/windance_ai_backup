"""Fixed local diagnostic job; explicit submit/status/cancel/result records."""
import hashlib,json,os,subprocess,sys,time,uuid,shutil,re
from pathlib import Path
IMAGE='sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f'
root=Path(__file__).resolve().parent
mode=sys.argv[1]
assert mode in ('diagnose','timeout','cancel','crash-test')
logical_id=sys.argv[2]
assert re.fullmatch('[0-9a-f]{32}',logical_id)
assert len(sys.argv) in (5,6) and all(re.fullmatch('[0-9a-f]{64}',v) for v in sys.argv[3:5])
retain=len(sys.argv)==6
assert not retain or sys.argv[5]=='--retain-container'
job=root/('job-'+logical_id);job.mkdir(mode=0o700)
inputs=job/'inputs';inputs.mkdir(mode=0o755)
hashes={}
for filename in ('bounded_diagnosis_worker.py','failure.json'):
    data=(root/filename).read_bytes()
    assert len(data)<=65536
    (inputs/filename).write_bytes(data);(inputs/filename).chmod(0o444)
    hashes[filename]=hashlib.sha256(data).hexdigest()
(job/'input-manifest.json').write_text(json.dumps(hashes,sort_keys=True))
assert hashes['failure.json']==sys.argv[3] and hashes['bounded_diagnosis_worker.py']==sys.argv[4]
name='windance-diagnosis-'+uuid.uuid4().hex
events=[];start=time.monotonic();container=None
def record(state,**extra):
    events.append({'state':state,'elapsed_seconds':round(time.monotonic()-start,3),**extra})
    tmp=job/'status.tmp'
    with tmp.open('w') as stream:
        json.dump(events,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,job/'status.json')
args=['docker','create','--name',name,'--pull=never','--network=none','--read-only',
      '--cap-drop=ALL','--security-opt=no-new-privileges','--user=65534:65534',
      '--pids-limit=16','--memory=128m','--cpus=0.5','--log-driver=none',
      '--mount',f'type=bind,src={inputs},dst=/evidence,readonly',
      '--label','windance.diagnostic=isolated-r2',
      '--entrypoint','timeout',IMAGE,'--signal=KILL','3s','python','-B',
      '/evidence/bounded_diagnosis_worker.py','timeout' if mode=='crash-test' else mode]
try:
    record('submitted',limits={'worker_seconds':3,'diagnostic_invocations':1,'model_calls':0,'network':'none','memory_mb':128,'cpus':0.5})
    container=subprocess.check_output(args,text=True,timeout=15).strip()
    with (job/'container.json').open('w') as stream:
        json.dump({'id':container,'name':name,'image':IMAGE},stream);stream.flush();os.fsync(stream.fileno())
    config=json.loads(subprocess.check_output(['docker','inspect',container],text=True,timeout=5))[0]
    host=config['HostConfig']
    assert host['NetworkMode']=='none' and host['ReadonlyRootfs'] and host['Memory']==128*1024*1024
    assert host['PidsLimit']==16 and host['NanoCpus']==500000000
    assert config['Config']['User']=='65534:65534' and all(not m['RW'] for m in config['Mounts'])
    assert 'ALL' in host['CapDrop'] and 'no-new-privileges' in host['SecurityOpt']
    assert config['Config']['Entrypoint']==['timeout'] and config['Config']['Cmd'][:2]==['--signal=KILL','3s']
    if mode=='crash-test':
        subprocess.run(['docker','start',container],check=True,stdout=subprocess.DEVNULL,timeout=5)
        actual=json.loads(subprocess.check_output(['docker','inspect',container],text=True,timeout=5))[0]
        assert actual['State']['Running'] is True
        record('running',container_settings_verified=True,crash_injection=True)
        print(json.dumps({'job':str(job)}),flush=True)
        os._exit(73)
    record('running',container_settings_verified=True)
    proc=subprocess.Popen(['docker','start','-a',container],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        out,err=proc.communicate(timeout=0.5 if mode=='cancel' else 5)
    except subprocess.TimeoutExpired:
        record('cancel_requested' if mode=='cancel' else 'deadline_exceeded')
        subprocess.run(['docker','kill',container],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=5)
        out,err=proc.communicate(timeout=5)
        status='cancelled' if mode=='cancel' else 'timed_out'
    else:
        assert len(out)<=65536 and len(err)<=65536
        if mode=='timeout' and proc.returncode==137:
            status='timed_out'
        else:
            assert proc.returncode==0
            result=json.loads(out);(job/'result.json').write_text(json.dumps(result,indent=2));status='completed'
    actual=json.loads(subprocess.check_output(['docker','inspect',container],text=True,timeout=5))[0]
    assert actual['State']['Running'] is False
    assert all(hashlib.sha256((inputs/n).read_bytes()).hexdigest()==digest for n,digest in hashes.items())
    terminal={'job_id':logical_id,'container_id':container,'image':actual['Image'],'worker_running':False,
              'exit_code':actual['State']['ExitCode'],'outcome':status,'input_hashes':hashes,
              'result_sha256':hashlib.sha256((job/'result.json').read_bytes()).hexdigest() if (job/'result.json').exists() else None}
    with (job/'terminal.json').open('w') as stream:
        json.dump(terminal,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
    record(status,worker_stopped_verified=True)
except Exception:
    record('failed',detail='Job control or verification failed; do not infer completion')
    raise
finally:
    if container and not retain:
        subprocess.run(['docker','rm','-f','-v',container],check=True,stdout=subprocess.DEVNULL,timeout=10)
        record('cleaned',previous_state=events[-1]['state'])
print(json.dumps({'job':str(job),'events':events,'result_available':(job/'result.json').exists()}))
