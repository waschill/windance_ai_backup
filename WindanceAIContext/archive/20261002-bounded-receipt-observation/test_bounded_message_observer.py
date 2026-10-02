"""Supervisor fault injection in a disposable module copy, no real DB/sender."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time

results=[]
with tempfile.TemporaryDirectory(prefix='windance-observer-bound-') as tmp:
    root=Path(tmp)
    source=Path(__file__).with_name('bounded_message_observer.py')
    copy=root/'bounded_message_observer.py'
    copy.write_bytes(source.read_bytes())
    spec=importlib.util.spec_from_file_location('bounded_test',copy)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Parent code is already loaded. Replace only the disposable child target to
    # simulate faults at its process boundary, not production source replacement.
    cases={
      'malformed':"print('PRIVATE_SENTINEL not json')",
      'wrong_receipt':"print('{\"status\":\"delivered\",\"evidence\":\"local_messages_flags\",\"message_rowid\":true}')",
      'private_reason':"print('{\"status\":\"unavailable\",\"reason\":\"PRIVATE_SENTINEL\"}')",
      'oversized':"print('x'*5000)",
      'crash':"import os; os._exit(17)",
      'timeout':"import os,time; from pathlib import Path; Path(__file__).with_suffix('.pid').write_text(str(os.getpid())); time.sleep(60)",
    }
    for case,body in cases.items():
        copy.write_text(body)
        start=time.monotonic()
        result=module.observe_bounded(root/'not-created.db','synthetic-owner','PRIVATE_SENTINEL',0,root/'unused.whl')
        elapsed=time.monotonic()-start
        assert result==module.FAIL,case
        assert 'PRIVATE_SENTINEL' not in json.dumps(result)
        assert not (root/'not-created.db').exists()
        if case=='timeout':
            assert 14<=elapsed<20,elapsed
            pid=int(copy.with_suffix('.pid').read_text())
            try:os.kill(pid,0)
            except ProcessLookupError:pass
            else:raise AssertionError('worker survived timeout')
        results.append({'case':case,'status':result['status'],'seconds':round(elapsed,3)})
print(json.dumps({'status':'passed','cases':results,'real_sends':0,'private_output_excluded':True}))
