"""Exercise real launchd recovery on a disposable service, never production."""
import json
import os
import plistlib
import subprocess
import time
from pathlib import Path
import remote_ops

label='com.windance.supervisor-recovery-canary'
domain=f'gui/{os.getuid()}'
path=Path.home()/'services/windance-supervisor'/f'{label}.plist'
path.write_bytes(plistlib.dumps({'Label':label,'ProgramArguments':['/bin/sleep','180'], 'RunAtLoad':False}))
subprocess.run(['/bin/launchctl','bootstrap',domain,str(path)],check=True)
try:
    remote_ops.HERALD=True
    remote_ops.LABELS={'harness':label}
    remote_ops.probe=lambda:{'checks':{'harness':False}}
    before=remote_ops.launch(label)
    assert before['loaded'] and not before['pid']
    receipt=remote_ops.recover('restart_harness')
    time.sleep(1)
    after=remote_ops.launch(label)
    assert receipt['performed'] and after['pid']>0
    print(json.dumps({'test':'real_launchd_recovery','before':before,'after':after,'receipt':receipt,'production_services_changed':False}))
finally:
    subprocess.run(['/bin/launchctl','bootout',domain+'/'+label],check=True)
