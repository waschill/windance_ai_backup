"""Temporary heartbeat-only launchd fixture; never targets production labels."""
import json,os,plistlib,re,select,subprocess,sys,time
from pathlib import Path
from receiver_pause_guard import inspect
if len(sys.argv)>1 and sys.argv[1]=='heartbeat':
    marker=Path(sys.argv[2]);value=sys.argv[3]
    while True:
        marker.write_text(value);time.sleep(.1)

root=Path.home()/'backups/receiver-launchd-fixture-20261002'
root.mkdir(mode=0o700,exist_ok=False)
label='com.windance.receipt-handoff-fixture-20261002';domain=f'gui/{os.getuid()}'
target=domain+'/'+label;plist=root/'fixture.plist';marker=root/'heartbeat'
python='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python'
assert subprocess.run(['launchctl','print',target],capture_output=True).returncode!=0
guard=None;bootout=None;elapsed=None
def job():return subprocess.run(['launchctl','print',target],capture_output=True,text=True)
def wait_for(predicate,seconds=5):
    end=time.monotonic()+seconds
    while not predicate():
        if time.monotonic()>end:raise AssertionError('launch fixture timeout')
        time.sleep(.05)
def write_plist(value):
    plist.write_bytes(plistlib.dumps({'Label':label,'ProgramArguments':[python,'-B',str(Path(__file__).resolve()),'heartbeat',str(marker),value],
                                      'RunAtLoad':True,'KeepAlive':True,'StandardOutPath':str(root/'stdout'),'StandardErrorPath':str(root/'stderr')}))
try:
    write_plist('old')
    subprocess.run(['launchctl','bootstrap',domain,str(plist)],check=True,capture_output=True,timeout=5)
    wait_for(lambda:marker.exists() and marker.read_text()=='old')
    old_pid=int(re.search(r'(?m)^\s*pid = (\d+)',job().stdout).group(1))
    identity=inspect(old_pid)[0]
    guard=subprocess.Popen([python,'-B',str(Path(__file__).with_name('receiver_pause_guard.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
    guard.stdin.write((json.dumps({'pid':old_pid,'identity':identity,'seconds':15})+'\n').encode());guard.stdin.flush()
    assert select.select([guard.stdout],[],[],3)[0]
    assert json.loads(guard.stdout.readline())['status']=='paused'
    started=time.monotonic()
    bootout=subprocess.Popen(['launchctl','bootout',target],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    bootout.wait(timeout=12);elapsed=round(time.monotonic()-started,3)
    assert bootout.returncode==0 and job().returncode!=0
    # It is not sufficient for the launchctl command alone to return success.
    wait_for(lambda:inspect(old_pid) is None,2)
    guard.stdin.close();guard.wait(timeout=3);assert guard.returncode==0
    write_plist('new')
    subprocess.run(['launchctl','bootstrap',domain,str(plist)],check=True,capture_output=True,timeout=5)
    wait_for(lambda:marker.read_text()=='new')
    new_pid=int(re.search(r'(?m)^\s*pid = (\d+)',job().stdout).group(1))
    assert new_pid!=old_pid
finally:
    if guard is not None:
        if guard.stdin and not guard.stdin.closed:guard.stdin.close()
        guard.wait(timeout=4);guard.stdout.close()
    if bootout is not None and bootout.poll() is None:bootout.wait(timeout=10)
    subprocess.run(['launchctl','bootout',target],capture_output=True,timeout=10)
    assert job().returncode!=0
print(json.dumps({'status':'passed','stopped_fixture_bootout_seconds':elapsed,'same_label_replacement':True,'old_process_exit_verified':True,'temporary_job_removed':True,'production_labels_changed':0,'real_sends':0}))
