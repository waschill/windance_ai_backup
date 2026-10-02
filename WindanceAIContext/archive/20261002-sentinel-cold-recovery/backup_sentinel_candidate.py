"""Private original/candidate recovery bundle, including synthetic journal only."""
import datetime,hashlib,json,os,shutil,sqlite3,zipfile
from pathlib import Path
from daily_report_journal import provision,run_daily

root=Path('/Users/herald/backups/sentinel-caller-recovery-20261002-r1')
root.mkdir(mode=0o700,exist_ok=False);bundle=root/'bundle';bundle.mkdir(mode=0o700)
stage=Path('/tmp/windance-caller-stage-20261002')
original=Path('/Users/herald/services/sentinel-router-logs/sentinel_daily_router_review.py')
plist=Path('/Users/herald/Library/LaunchAgents/com.windance.sentinel-router-review.plist')
assert hashlib.sha256(original.read_bytes()).hexdigest()=='1f8f1aaa283bd57ecd2895d13b81e2de150a2a0294320bc9de7d1d113078f6a1'
assert hashlib.sha256(plist.read_bytes()).hexdigest()=='81a4ec77cc523601c20622327314b49593d5fb596f0e772c22d33c6152459c96'
shutil.copyfile(original,bundle/'original_sentinel.py');shutil.copyfile(plist,bundle/'original_schedule.plist')
for name in ('sentinel_daily_router_review_durable.py','daily_report_journal.py','receipt_report_transport.py',
             'outbox_wire_protocol.py','test_sentinel_durable_main.py','test_daily_report_journal.py','test_daily_report_crash.py'):
    shutil.copyfile(stage/name,bundle/name)
assert hashlib.sha256((bundle/'sentinel_daily_router_review_durable.py').read_bytes()).hexdigest()=='608070e958e7226b831c02f393c690db088878cffc1c8e88e66e3705ffbe7d9b'
sample=root/'synthetic-source.db';provision(sample)
receipt={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}
run_daily(sample,'synthetic-held','2026-10-02','synthetic-owner',lambda:('synthetic blocked',False),lambda *a,**k:{'ok':False})
run_daily(sample,'synthetic-done','2026-10-02','synthetic-owner',lambda:('synthetic available',True),lambda *a,**k:receipt)
with sqlite3.connect(str(sample)) as source,sqlite3.connect(str(bundle/'synthetic-reports.db')) as destination:source.backup(destination)
for p in bundle.iterdir():os.chmod(p,0o600)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.iterdir())}
(bundle/'release-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2));os.chmod(bundle/'release-manifest.json',0o600)
archive=root/'sentinel-private.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(bundle.iterdir()):z.write(p,p.name)
os.chmod(archive,0o600)
assert original.read_bytes()==(bundle/'original_sentinel.py').read_bytes()
assert plist.read_bytes()==(bundle/'original_schedule.plist').read_bytes()
print(json.dumps({'path':str(root),'files':len(manifest),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'live_files_unchanged':True}))
