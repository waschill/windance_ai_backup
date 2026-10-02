"""Verify and test exact restored archive; --worker explicitly runs synthetic worker."""
import hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath
archive_path=Path(sys.argv[1]);expected=sys.argv[2]
assert hashlib.sha256(archive_path.read_bytes()).hexdigest()==expected
with tempfile.TemporaryDirectory() as directory,zipfile.ZipFile(archive_path) as archive:
    root=Path(directory)
    manifest=json.loads(archive.read('manifest.json'));pins=manifest['files']
    assert len(archive.namelist())==len(set(archive.namelist()))
    assert set(archive.namelist())==set(pins)|{'manifest.json'}
    for name,digest in pins.items():
        relative=PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
        assert relative.parts[0] in ('AL','HERALD','validation')
        assert archive.getinfo(name).file_size<=65536
        data=archive.read(name);assert hashlib.sha256(data).hexdigest()==digest
        destination=root.joinpath(*relative.parts);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        if name.endswith('.py'):compile(data,name,'exec')
    env=dict(os.environ,PYTHONPATH=str(root/'HERALD'),PYTHONDONTWRITEBYTECODE='1')
    for test in ('test_diagnostic_job_api.py','test_diagnostic_request_bounds.py','test_diagnostic_bounded_process.py','test_diagnostic_admission.py','test_diagnostic_consumer.py'):
        subprocess.run([sys.executable,'-B',str(root/'validation'/test)],env=env,cwd=root,check=True,timeout=30)
    worker='--worker' in sys.argv[3:]
    if worker:
        subprocess.run([sys.executable,'-B',str(root/'validation'/'test_diagnostic_http_worker.py'),pins['AL/bounded_diagnosis_worker.py'],pins['AL/bounded_diagnosis_job_r4.py'],pins['AL/failure.json']],env=env,cwd=root,check=True,timeout=75)
    for name,digest in pins.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
    print(json.dumps({'revision':manifest['revision'],'files_verified':len(pins),'archive_sha256':expected,'restored_api_tests':True,'restored_full_worker_test':worker,'post_test_source_hashes_unchanged':True}))


