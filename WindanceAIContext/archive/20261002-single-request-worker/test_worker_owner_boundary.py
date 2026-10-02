"""Exercise single-request admission without any transport capability."""
import fcntl,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
from receipt_request_worker import process_one,DAEMON_SHA256

source=Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest()==DAEMON_SHA256
spec=importlib.util.spec_from_file_location('owner_test_host',source)
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
def forbid(*args,**kwargs):raise AssertionError('unexpected_send')
host.send_one=forbid
with tempfile.TemporaryDirectory(prefix='windance-worker-owner-') as tmp:
    root=Path(tmp);host.ROOT=root;host.QUEUE=root/'queue';host.RESULTS=root/'results';host.LOG=root/'log'
    host.QUEUE.mkdir();host.RESULTS.mkdir()
    request=host.QUEUE/'synthetic.json'
    request.write_text(json.dumps({'to':'synthetic-owner','chunks':['synthetic'],'sms':False}))
    original=request.read_bytes()
    with (root/'owner.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert process_one(host,'synthetic',root/'missing.db',root/'missing.whl')=='owner_busy'
        assert request.read_bytes()==original and not list(host.RESULTS.iterdir())
    # Runtime must not manufacture a journal; quarantine before any send.
    assert process_one(host,'synthetic',root/'missing.db',root/'missing.whl')=='processed'
    assert not (root/'journal.db').exists()
    assert (root/'uncertain/synthetic.json').read_bytes()==original
    assert json.loads((host.RESULTS/'synthetic.json').read_text())['status']=='uncertain'
    assert process_one(host,'synthetic',root/'missing.db',root/'missing.whl')=='request_absent'
    try:process_one(host,'../escape',root/'missing.db',root/'missing.whl')
    except ValueError:pass
    else:raise AssertionError('invalid_id_admitted')
print(json.dumps({'status':'passed','owner_contention_unchanged':True,'missing_journal_quarantined':True,'absent_request_no_replay':True,'invalid_id_rejected':True,'real_sends':0}))
