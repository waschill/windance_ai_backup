"""Private coordinated caller code recovery; no live history or credentials."""
import hashlib,json,os,shutil,zipfile
from pathlib import Path
root=Path('/Users/herald/backups/report-callers-20261002-r1')
root.mkdir(mode=0o700,exist_ok=False)
bundle=root/'bundle';bundle.mkdir(mode=0o700)
stage=Path('/tmp/windance-caller-stage-20261002')
originals={
 'original_report.py':('/Users/herald/bin/windance_report_send.py','aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'),
 'original_manager.py':('/Users/herald/services/vega-manager/manager.py','0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'),
 'original_sentinel.py':('/Users/herald/services/sentinel-router-logs/sentinel_daily_router_review.py','1f8f1aaa283bd57ecd2895d13b81e2de150a2a0294320bc9de7d1d113078f6a1'),
 'original_capture.py':('/Users/herald/services/capture-review-reminder/capture_review_reminder.py','763a096d0a61319ea4c732ae24119b2f642adc847570585c7fa6f05802753900'),
 'original_capture.plist':('/Users/herald/Library/LaunchAgents/com.windance.capture-review-reminder.plist','d49edec0a24fc81f2aca8dac63e4dd0e3a6fc8e5b84bb800b692164e573b81e2'),
 'original_sentinel.plist':('/Users/herald/Library/LaunchAgents/com.windance.sentinel-router-review.plist','81a4ec77cc523601c20622327314b49593d5fb596f0e772c22d33c6152459c96')}
for name,(path,digest) in originals.items():
    data=Path(path).read_bytes();assert hashlib.sha256(data).hexdigest()==digest,name
    (bundle/name).write_bytes(data)
for name in ('windance_report_send_candidate_r2.py','sentinel_daily_router_review_durable.py',
             'capture_review_reminder_durable.py','capture-review-runtime-candidate.plist',
             'daily_report_journal.py','receipt_report_transport.py','outbox_wire_protocol.py',
             'test_manager_report_pipeline.py','test_sentinel_durable_main.py','test_capture_durable_main.py',
             'test_daily_report_journal.py','test_daily_report_crash.py','test_report_wire_contract.py'):
    shutil.copyfile(stage/name,bundle/name)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.iterdir())}
(bundle/'release-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2))
for p in bundle.iterdir():os.chmod(p,0o600)
archive=root/'report-callers-private.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(bundle.iterdir()):z.write(p,p.name)
os.chmod(archive,0o600)
for name,(path,digest) in originals.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
print(json.dumps({'files':len(manifest),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'live_sources_unchanged':True}))
