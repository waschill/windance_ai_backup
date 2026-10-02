"""Synthetic guardian timing instrumentation in an isolated source copy."""
import importlib.util,json
from pathlib import Path
import tempfile,time

with tempfile.TemporaryDirectory(prefix='windance-guardian-timing-') as tmp:
    root=Path(tmp)
    source=Path(__file__).parent
    (root/'bounded_outbox_request.py').write_bytes((source/'bounded_outbox_request.py').read_bytes())
    (root/'outbox_group_worker.py').write_bytes((source/'outbox_group_worker.py').read_bytes())
    guardian=(source/'outbox_request_guardian.py').read_text()
    guardian=guardian.replace('def finish(result):','def finish(result):\n    from pathlib import Path\n    Path(__file__).with_suffix(".timing").write_text(json.dumps({"at":time.monotonic(),"pid":os.getpid(),"pgid":os.getpgrp(),"result":result}))')
    (root/'outbox_request_guardian.py').write_text(guardian)
    worker=root/'worker.py';worker.write_text('import time,os,json\nfrom pathlib import Path\nr=Path(__file__).parent\n(r/"worker_started").write_text(json.dumps({"at":time.monotonic(),"pid":os.getpid(),"pgid":os.getpgrp()}))\ntime.sleep(0.8)\n(r/"late_effect").write_text("synthetic")\ntime.sleep(60)\n')
    spec=importlib.util.spec_from_file_location('isolated_supervisor',root/'bounded_outbox_request.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    import sys
    results=[]
    for _ in range(5):
        trace=root/'outbox_request_guardian.timing'
        if trace.exists():trace.unlink()
        for name in ('worker_started','late_effect'):
            if (root/name).exists():(root/name).unlink()
        start=time.monotonic()
        result=module.run_bounded([sys.executable,str(worker)],seconds=0.3)
        finished=time.monotonic()
        record=json.loads(trace.read_text()) if trace.exists() else None
        time.sleep(0.85)
        results.append({'total_seconds':round(finished-start,4),'guardian_finish_seconds':round(record['at']-start,4) if record else None,
                        'worker_started':(root/'worker_started').exists(),'same_group_as_guardian':(json.loads((root/'worker_started').read_text())['pgid']==record['pgid']) if record and (root/'worker_started').exists() else None,'late_effect_absent':not (root/'late_effect').exists(),'result':result})
        if (root/'late_effect').exists():
            print(json.dumps({'status':'failed','reason':'synthetic_effect_after_deadline','samples':results,'real_sends':0}))
            raise SystemExit(1)
    print(json.dumps({'samples':results,'real_sends':0}))
