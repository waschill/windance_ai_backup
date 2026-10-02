import json,subprocess,time
payload={'to':'synthetic-owner','chunks':['synthetic disconnect'],'sms':False};key='synthetic-disconnect'
ssh=['/usr/bin/ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','SAL','/usr/bin/python3','-B']
helper='/tmp/ssh_disconnect_fixture.py'
def inspect(mode):
    r=subprocess.run(ssh+[helper,'inspect',mode],capture_output=True,text=True,timeout=5)
    assert r.returncode==0
    return json.loads(r.stdout)
results=[]
for mode in ('query','submit'):
    client=subprocess.Popen(ssh+[helper,'endpoint',mode],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        client.stdin.write(json.dumps({'key':key,'payload':payload}).encode());client.stdin.close()
        deadline=time.monotonic()+1.5
        while True:
            before=inspect(mode)
            if before['queue_count']==1 and before['worker_running'] and before['endpoint_running']:break
            assert client.poll() is None and time.monotonic()<deadline
        assert client.poll() is None
        client.kill();client.wait(timeout=2)
        deadline=time.monotonic()+5
        while True:
            after=inspect(mode)
            if not after['endpoint_running'] and not after['worker_running']:break
            assert time.monotonic()<deadline,'remote processes survived deadline'
            time.sleep(.1)
        assert after['queue_count']==1 and before['queue_hashes']==after['queue_hashes']
        retry=subprocess.run(ssh+['/tmp/outbox_protocol_cli.py','--root','/tmp/windance-disconnect-20261002/'+mode,
                                 '--mode','submit','--wait-seconds','.3'],
                             input=json.dumps({'key':key,'payload':payload}),capture_output=True,text=True,timeout=5)
        assert retry.returncode==14,(mode,retry.returncode)
        final=inspect(mode)
        assert final['queue_count']==1 and final['queue_hashes']==before['queue_hashes']
        results.append({'mode':mode,'live_ssh_interrupted':True,'remote_workers_stopped':True,'one_request_after_reconnect':True})
    finally:
        if client.poll() is None:client.kill();client.wait(timeout=2)
print(json.dumps({'status':'passed','cases':results,'real_sends':0}))
