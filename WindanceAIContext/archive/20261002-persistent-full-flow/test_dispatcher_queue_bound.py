import json,tempfile
from pathlib import Path
from receipt_outbox_dispatcher import select_request
with tempfile.TemporaryDirectory(prefix='windance-queue-bound-') as tmp:
    root=Path(tmp)
    assert select_request(root,'',limit=3)==(None,False)
    for name in ('c.json','a.json','b.json'):(root/name).write_text('{}')
    assert select_request(root,'',limit=3)==('a',False)
    assert select_request(root,'a',limit=3)==('b',False)
    assert select_request(root,'z',limit=3)==('a',False)
    (root/'partial.tmp').write_text('synthetic')
    assert select_request(root,'',limit=3)==(None,True)
    assert select_request(root,'',limit=4)==('a',False)
print(json.dumps({'status':'passed','bounded_inventory_overflow_holds':True,'cursor_rotation_preserved':True,'sends':0}))
