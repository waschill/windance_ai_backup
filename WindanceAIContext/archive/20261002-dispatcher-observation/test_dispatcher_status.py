import json,tempfile
from pathlib import Path
from receipt_outbox_dispatcher import Status
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);status=Status(root)
    status.write('idle');initial=status.path.read_bytes()
    status.write('idle');assert status.path.read_bytes()==initial
    status.updated-=31
    status.write('idle');assert status.path.read_bytes()!=initial
    status.write('held',reason='queue_inventory_limit')
    assert json.loads(status.path.read_text())['reason']=='queue_inventory_limit'
    status.write('working',started_unix=123,request_seconds=600)
    value=json.loads(status.path.read_text())
    assert value['state']=='working' and value['request_seconds']==600
    assert not list(root.glob('*.tmp'))
print(json.dumps({'status':'passed','checks':['idle_write_throttling','refresh','hold','active_budget','atomic_replacement'],'real_sends':0}))
