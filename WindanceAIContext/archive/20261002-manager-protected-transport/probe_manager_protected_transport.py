"""SAL -> HERALD manager health over temporary strict-host-key SSH forwarding.

No keys are read/exported; no config or service change. Only GET /health.
"""
import datetime,json,socket,subprocess,time,urllib.request

port=18797
with socket.socket() as guard:
    guard.bind(('127.0.0.1',port))
command=['/usr/bin/ssh','-N','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
         '-o','ExitOnForwardFailure=yes','-o','ConnectTimeout=8','-o','ControlMaster=no',
         '-o','ControlPath=none','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',
         '-L',f'127.0.0.1:{port}:127.0.0.1:8797','HERALD']
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'purpose':'manager health only','strict_host_key':True,'batch_auth':True,
         'local_bind':'127.0.0.1','persistent_configuration_changed':False,
         'model_calls':0,'dispatches':0,'sends':0}
process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
try:
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        if process.poll() is not None:
            # Do not emit raw SSH errors or authentication details.
            receipt['ssh_exit']=process.returncode
            raise RuntimeError('Strict noninteractive SSH forwarding failed')
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=2) as response:
                value=json.load(response)
                receipt['health_http_status']=response.status
                receipt['health_keys']=sorted(value.keys())
                receipt['health_ok']=value.get('ok')
                receipt['service']=value.get('service')
                receipt['tunnel_live_during_health']=process.poll() is None
                break
        except OSError:
            time.sleep(.25)
    else:raise RuntimeError('No manager health response within bound')
except Exception as exc:
    receipt['failure_type']=type(exc).__name__
finally:
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    if process.stderr:
        diagnostic=process.stderr.read().decode(errors='replace').lower()
        receipt['ssh_failure_class']=(
            'host_key_verification' if 'host key verification failed' in diagnostic else
            'authentication' if 'permission denied' in diagnostic else
            'connection_refused' if 'connection refused' in diagnostic else
            'local_bind' if 'address already in use' in diagnostic else
            'timeout' if 'timed out' in diagnostic else
            'none' if not diagnostic else 'other')
        process.stderr.close()
    receipt['owned_tunnel_process_stopped']=process.poll() is not None
    with socket.socket() as check:
        receipt['local_port_closed']=check.connect_ex(('127.0.0.1',port)) != 0
print(json.dumps(receipt))
if receipt.get('health_http_status') != 200 or not receipt['local_port_closed']:
    raise SystemExit(1)
