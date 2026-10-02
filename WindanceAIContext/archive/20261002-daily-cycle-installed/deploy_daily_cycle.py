from contextlib import closing
import datetime,hashlib,json,os,re,shutil,sqlite3,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
home=Path('/Users/herald');stage=Path('/tmp/windance-caller-stage-20261002');backup=home/'backups/daily-cycle-deploy-20261002'
jobs={'capture':('capture-review-reminder','capture_review_reminder.py','capture_review_reminder_cycle.py','capture-report-delivery','com.windance.capture-review-reminder',19,0,'cc4b2e0e2271e2e7b0a236f0cdce309206a107c75ff7eeadbcce0afd0df16d6d','a7ab085cc89bf5cc4a7cba7bfa2a9b03733fab57c3311e9107d0ba38963a805a'),
      'sentinel':('sentinel-router-logs','sentinel_daily_router_review.py','sentinel_daily_router_review_cycle.py','sentinel-report-delivery','com.windance.sentinel-router-review',6,50,'608070e958e7226b831c02f393c690db088878cffc1c8e88e66e3705ffbe7d9b','f23e296237b6439656b735a13cd8c19700b45671f5744d9ebc2360dadc64b2b8')}
new_helpers={'receipt_report_transport.py':'16a24617694efdd1ea19b094b0473cb896ad5050b6c66fdfc7871a4c033742fe','daily_report_cycle.py':'978fdda1be109cc17d831788969de5bef669d808a63e270ebb00789fe4fd551d'}
old_manifest=json.loads((home/'backups/report-callers-20261002-r2/restored/release-manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def quiet(label):
    r=subprocess.run(['launchctl','print','user/501/'+label],capture_output=True,text=True,timeout=3)
    assert r.returncode==0 and not re.search(r'(?m)^\s*pid = ',r.stdout)
    runs=re.search(r'(?m)^\s*runs = (\d+)',r.stdout);assert runs is None or int(runs.group(1))==0
def empty(path):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as c:
        assert c.execute('PRAGMA user_version').fetchone()[0]==2 and c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0
def preflight():
    now=datetime.datetime.now(ZoneInfo('America/Denver'));assert 5<=now.hour<22
    for n,h in new_helpers.items():assert sha(stage/n)==h
    for name,(folder,source,candidate,journal,label,hour,minute,old,new) in jobs.items():
        service=home/'services'/folder;assert sha(service/source)==old and sha(stage/candidate)==new
        assert sha(service/'receipt_report_transport.py')==old_manifest['receipt_report_transport.py']
        assert not (service/'daily_report_cycle.py').exists()
        assert abs(now.hour*60+now.minute-(hour*60+minute))>3
        quiet(label);empty(home/'.local/share'/journal/'reports.db')
    r=subprocess.run(['ssh','SAL','python3','-B','/tmp/verify_installed_receipt_receiver.py'],capture_output=True,text=True,timeout=8)
    assert r.returncode==0 and json.loads(r.stdout)['warden_pause_preserved']
preflight();mode=sys.argv[1]
if mode=='backup':
    backup.mkdir(mode=0o700,exist_ok=False);files={n:stage/n for n in new_helpers}
    for name,(folder,source,candidate,journal,label,*_) in jobs.items():
        service=home/'services'/folder
        files.update({name+'.original.py':service/source,name+'.candidate.py':stage/candidate,name+'.transport.original.py':service/'receipt_report_transport.py',name+'.plist':home/'Library/LaunchAgents'/(label+'.plist')})
        path=home/'.local/share'/journal/'reports.db'
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as c,closing(sqlite3.connect(backup/(name+'.db'))) as b:
            c.backup(b);assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and b.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0
        shutil.copyfile(backup/(name+'.db'),backup/(name+'.cold.db'))
        files[name+'.db']=backup/(name+'.db');files[name+'.cold.db']=backup/(name+'.cold.db')
    for n,p in files.items():
        if p!=backup/n:shutil.copyfile(p,backup/n)
        (backup/n).chmod(0o600)
    receipt={'files':{n:sha(backup/n) for n in files}}
    (backup/'backup-receipt.json').write_text(json.dumps(receipt));preflight()
    print(json.dumps({'files':len(files),'journals_empty':True,'backup':str(backup)}))
elif mode=='deploy':
    receipt=json.loads((backup/'backup-receipt.json').read_text())
    assert json.loads((backup/'hal-verification.json').read_text())==receipt
    assert all(sha(backup/n)==v for n,v in receipt['files'].items())
    for name,(folder,source,candidate,journal,label,*_) in jobs.items():
        service=home/'services'/folder;quiet(label)
        for src,target in [(stage/n,service/n) for n in new_helpers]+[(stage/candidate,service/source)]:
            temp=target.with_name(target.name+'.cycle-stage')
            with temp.open('xb') as f:f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
            temp.chmod(0o600);os.replace(temp,target)
        assert sha(service/source)==sha(stage/candidate) and all(sha(service/n)==v for n,v in new_helpers.items())
        assert sha(home/'Library/LaunchAgents'/(label+'.plist'))==receipt['files'][name+'.plist']
        quiet(label);empty(home/'.local/share'/journal/'reports.db')
    result={'status':'installed_waiting','jobs':list(jobs),'schedules_unchanged':True,'journals_empty':True,'runs':0,'manual_sends':0}
    (backup/'deployment-receipt.json').write_text(json.dumps(result));print(json.dumps(result))
else:raise ValueError('unknown_mode')
