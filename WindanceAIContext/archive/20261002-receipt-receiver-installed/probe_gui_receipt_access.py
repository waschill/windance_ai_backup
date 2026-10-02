"""Read-only Messages metadata from a temporary same-interpreter GUI job."""
import json,os,plistlib,sqlite3,subprocess,sys,time
from pathlib import Path
root=Path.home()/'backups/receipt-gui-access-20261002'
if len(sys.argv)>1 and sys.argv[1]=='probe':
    try:
        with sqlite3.connect((Path.home()/'Library/Messages/chat.db').as_uri()+'?mode=ro',uri=True,timeout=1) as c:
            c.execute('SELECT ROWID FROM message LIMIT 1').fetchone()
            columns={r[1] for r in c.execute('PRAGMA table_info(message)')}
            assert {'guid','is_from_me','is_sent','is_delivered','date_delivered','error','attributedBody'}<=columns
        result={'readable':True,'receipt_columns_present':True,'message_content_read':False}
    except Exception as e:result={'readable':False,'error_type':type(e).__name__}
    (root/'result.json').write_text(json.dumps(result));raise SystemExit(0 if result['readable'] else 1)
root.mkdir(mode=0o700,exist_ok=False)
label='com.windance.receipt-access-fixture-20261002';domain=f'gui/{os.getuid()}';target=domain+'/'+label
assert subprocess.run(['launchctl','print',target],capture_output=True).returncode!=0
plist=root/'probe.plist'
plist.write_bytes(plistlib.dumps({'Label':label,'ProgramArguments':['/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python','-B',str(Path(__file__).resolve()),'probe'],'RunAtLoad':True,'KeepAlive':False,'StandardErrorPath':str(root/'stderr')}))
try:
    subprocess.run(['launchctl','bootstrap',domain,str(plist)],check=True,capture_output=True,timeout=5)
    end=time.monotonic()+5
    while not (root/'result.json').exists() and time.monotonic()<end:time.sleep(.05)
    result=json.loads((root/'result.json').read_text());assert result['readable'],result
finally:
    subprocess.run(['launchctl','bootout',target],capture_output=True,timeout=5)
    assert subprocess.run(['launchctl','print',target],capture_output=True).returncode!=0
print(json.dumps({**result,'temporary_job_removed':True,'real_sends':0,'production_service_changed':False}))
