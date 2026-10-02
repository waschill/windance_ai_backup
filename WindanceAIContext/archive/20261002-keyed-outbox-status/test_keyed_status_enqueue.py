"""Actual producer compatibility, temporary queue only; never invokes main/sender."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from keyed_outbox_status import lookup

source=Path(sys.argv[1])
assert hashlib.sha256(source.read_bytes()).hexdigest()=='382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f'
spec=importlib.util.spec_from_file_location('actual_producer',source)
producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)
with tempfile.TemporaryDirectory(prefix='windance-keyed-status-') as tmp:
    root=Path(tmp);producer.ROOT=root;producer.QUEUE=root/'queue';producer.RESULTS=root/'results'
    payload={'to':'synthetic-owner','chunks':['Synthetic café 😀'],'sms':False};key='synthetic-receipt-key'
    result,retained=producer.enqueue(payload,key)
    assert retained and lookup(root,key,payload)['status']=='pending'
    assert lookup(root,key,dict(payload,chunks=['changed']))['status']=='conflict'
    result.write_text('{"ok":true,"chunks":1}')
    original=result.read_bytes()
    assert lookup(root,key,payload)['status']=='legacy_submission'
    assert result.read_bytes()==original
    assert producer.enqueue(payload,key)==(result,True)
    assert len(list((root/'queue').glob('*.json')))==1
print(json.dumps({'status':'passed','actual_enqueue_unicode_identity':True,'legacy_result_not_deleted':True,'real_sends':0}))
