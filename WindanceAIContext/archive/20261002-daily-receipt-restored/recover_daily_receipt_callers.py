"""One-time source and future-calendar recovery; never manually executes reports."""
import datetime,hashlib,json,os,plistlib,re,shutil,sqlite3,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
home=Path('/Users/herald');stage=home/'backups/report-callers-20261002-r2/restored'
backup=home/'backups/daily-receipt-recovery-20261002'
helpers=['daily_report_journal.py','receipt_report_transport.py','outbox_wire_protocol.py']
jobs={
 'capture':{'folder':'capture-review-reminder','source':'capture_review_reminder.py','candidate':'capture_review_reminder_durable.py','label':'com.windance.capture-review-reminder','journal':'capture-report-delivery','hour':19,'minute':0,'original':'original_capture.py','plist':'original_capture.plist','candidate_plist':'capture-review-runtime-candidate.plist'},
 'sentinel':{'folder':'sentinel-router-logs','source':'sentinel_daily_router_review.py','candidate':'sentinel_daily_router_review_durable.py','label':'com.windance.sentinel-router-review','journal':'sentinel-report-delivery','hour':6,'minute':50,'original':'original_sentinel.py','plist':'original_sentinel.plist','candidate_plist':'original_sentinel.plist'}}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((stage/'release-manifest.json').read_text())
def run(*args):return subprocess.run(args,capture_output=True,text=True,timeout=5)
def check():
    current=datetime.datetime.now(ZoneInfo('America/Denver'));assert 5<=current.hour<22
    assert sha(home/'services/agent-harness/agent_harness.py')=='c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7'
    assert sha(home/'bin/windance_report_send.py')=='aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'
    for name,j in jobs.items():
        service=home/'services'/j['folder'];plist=home/'Library/LaunchAgents'/(j['label']+'.plist')
        assert sha(service/j['source'])==manifest[j['original']] and sha(plist)==manifest[j['plist']]
        assert sha(stage/j['candidate'])==manifest[j['candidate']] and sha(stage/j['candidate_plist'])==manifest[j['candidate_plist']]
        d=plistlib.loads(plist.read_bytes());assert d['RunAtLoad'] is False
        assert d['StartCalendarInterval']=={'Hour':j['hour'],'Minute':j['minute']}
        assert abs(current.hour*60+current.minute-(j['hour']*60+j['minute']))>3
        for domain in ('user/501','gui/501'):
            assert run('launchctl','print',domain+'/'+j['label']).returncode!=0
            disabled=run('launchctl','print-disabled',domain);assert disabled.returncode==0
            assert not re.search(re.escape('"'+j['label']+'"')+r'\s*=>\s*true',disabled.stdout)
        assert not (home/'.local/share'/j['journal']/'reports.db').exists()
        assert all(not (service/n).exists() and sha(stage/n)==manifest[n] for n in helpers)
    receiver=run('ssh','SAL','python3','-B','/tmp/verify_installed_receipt_receiver.py')
    assert receiver.returncode==0 and json.loads(receiver.stdout)['warden_pause_preserved']
check();mode=sys.argv[1]
if mode=='backup':
    backup.mkdir(mode=0o700,exist_ok=False)
    files={n:stage/n for n in helpers}
    for name,j in jobs.items():
        files.update({name+'.original.py':home/'services'/j['folder']/j['source'],name+'.candidate.py':stage/j['candidate'],
                      name+'.original.plist':home/'Library/LaunchAgents'/(j['label']+'.plist'),name+'.candidate.plist':stage/j['candidate_plist']})
    for name,path in files.items():shutil.copyfile(path,backup/name);(backup/name).chmod(0o600)
    receipt={'files':{n:sha(backup/n) for n in files},'original_jobs_unregistered':True}
    (backup/'backup-receipt.json').write_text(json.dumps(receipt));check()
    print(json.dumps({'backup':str(backup),'files':len(files),'no_live_source_changes':True}))
elif mode=='deploy':
    receipt=json.loads((backup/'backup-receipt.json').read_text())
    assert json.loads((backup/'hal-verification.json').read_text())['files']==receipt['files']
    assert all(sha(backup/n)==v for n,v in receipt['files'].items())
    sys.path.insert(0,str(stage));from daily_report_journal import provision
    results=[]
    for name,j in jobs.items():
        service=home/'services'/j['folder'];plist=home/'Library/LaunchAgents'/(j['label']+'.plist')
        journal=home/'.local/share'/j['journal']/'reports.db'
        journal.parent.mkdir(mode=0o700,exist_ok=False);provision(journal)
        for source,target in [(stage/n,service/n) for n in helpers]+[(stage/j['candidate'],service/j['source']),(stage/j['candidate_plist'],plist)]:
            temp=target.with_name(target.name+'.receipt-stage')
            with temp.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
            temp.chmod(0o600);os.replace(temp,target)
        assert run('plutil','-lint',str(plist)).returncode==0
        boot=run('launchctl','bootstrap','user/501',str(plist));assert boot.returncode==0,'registration failed; inspect partial state'
        status=run('launchctl','print','user/501/'+j['label']);assert status.returncode==0
        assert not re.search(r'(?m)^\s*pid = ',status.stdout),'unexpected immediate run'
        runs=re.search(r'(?m)^\s*runs = (\d+)',status.stdout);assert runs is None or int(runs.group(1))==0
        with sqlite3.connect(journal.as_uri()+'?mode=ro',uri=True) as c:assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0
        assert sha(service/j['source'])==manifest[j['candidate']] and sha(plist)==manifest[j['candidate_plist']]
        results.append({'job':name,'registered_domain':'user/501','calendar':{'Hour':j['hour'],'Minute':j['minute']},'runs':0,'journal_empty':True})
    result={'status':'registered_waiting','jobs':results,'manual_sends':0,'catchup_runs':0}
    (backup/'deployment-receipt.json').write_text(json.dumps(result));print(json.dumps(result))
else:raise ValueError('unknown_mode')
