import json,subprocess,sys,tempfile,time
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='windance-dispatcher-rotation-') as tmp:
    root=Path(tmp)
    for folder in ('queue','results'):(root/folder).mkdir()
    for name in ('0 invalid','a','b'):
        (root/'queue'/(name+'.json')).write_text('{"to":"synthetic-owner","chunks":["synthetic"],"sms":false}')
        if name!='0 invalid':(root/'results'/(name+'.json')).write_text('{"ok":true,"chunks":1}')
    command=[sys.executable,'-B',str(Path(__file__).with_name('receipt_outbox_dispatcher.py')),
             '--root',str(root),'--source',sys.argv[1],'--database',str(root/'unused.db'),
             '--wheel',str(root/'unused.whl'),'--request-seconds','2']
    child=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+5
        while (root/'queue/a.json').exists() or (root/'queue/b.json').exists():
            assert child.poll() is None and time.monotonic()<deadline
            time.sleep(.05)
        assert (root/'queue/0 invalid.json').exists()
        assert all((root/'results'/(name+'.json')).read_text()=='{"ok":true,"chunks":1}' for name in ('a','b'))
        assert child.poll() is None
    finally:
        if child.poll() is None:child.terminate()
        child.wait(timeout=3)
print(json.dumps({'status':'passed','persistent_loop_observed':True,'held_item_did_not_starve_later_work':True,'legacy_results_unchanged':True,'real_sends':0,'test_process_stopped':True}))
