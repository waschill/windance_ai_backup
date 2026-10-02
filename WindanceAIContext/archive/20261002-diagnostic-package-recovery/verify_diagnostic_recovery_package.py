"""Verify/extract only in a disposable directory; optional no-dispatch ASGI test."""
import hashlib,json,runpy,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath
p=Path(sys.argv[1]);expected=sys.argv[2]
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
with tempfile.TemporaryDirectory() as folder,zipfile.ZipFile(p) as archive:
    names=archive.namelist();assert len(names)==len(set(names))
    manifest=json.loads(archive.read('manifest.json'))
    assert set(names)==set(manifest['files'])|{'manifest.json'}
    assert all(i.file_size<=65536 for i in archive.infolist())
    for name,digest in manifest['files'].items():
        relative=PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
        assert relative.parts[0] in ('AL','HERALD','validation')
        data=archive.read(name);assert hashlib.sha256(data).hexdigest()==digest
        target=Path(folder).joinpath(*relative.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        if target.suffix=='.py':compile(data,str(target),'exec')
    ran=False
    if len(sys.argv)==4 and sys.argv[3]=='--test-api':
        sys.path.insert(0,str(Path(folder)/'HERALD'))
        runpy.run_path(str(Path(folder)/'validation'/'test_diagnostic_job_api.py'),run_name='__main__');ran=True
    print(json.dumps({'archive_sha256':expected,'files_verified':len(manifest['files']),'isolated_extraction':True,'api_recovery_test':ran,'worker_execution':False}))
