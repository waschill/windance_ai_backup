import contextlib,hashlib,importlib.util,io,json,sys
from pathlib import Path
source=Path('/tmp/windance-caller-stage-20261002/capture_review_reminder_durable.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='cc4b2e0e2271e2e7b0a236f0cdce309206a107c75ff7eeadbcce0afd0df16d6d'
spec=importlib.util.spec_from_file_location('capture_candidate',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
allowed=f'file:{m.DB}?mode=ro'
def guard(event,args):
    if event=='sqlite3.connect':
        target=args[0].decode('utf-8') if isinstance(args[0],bytes) else args[0]
        if target!=allowed:raise RuntimeError('unexpected_database')
    if event=='subprocess.Popen' or event in ('os.system','os.posix_spawn') or event.startswith('socket.'):
        raise RuntimeError('external_effect_blocked')
sys.addaudithook(guard)
assert not m.DELIVERY_JOURNAL.exists()
sys.argv=['capture_candidate','--dry-run'];output=io.StringIO()
with contextlib.redirect_stdout(output):code=m.main()
assert code==0 and output.getvalue().strip() and not m.DELIVERY_JOURNAL.exists()
print(json.dumps({'status':'passed','actual_readonly_count':True,'dry_run_exit':code,'delivery_history_not_created':True,'real_sends':0,'capture_text_read':False}))
