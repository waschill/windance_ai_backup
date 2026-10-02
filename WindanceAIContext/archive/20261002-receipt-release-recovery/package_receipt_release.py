"""Package only explicitly selected synthetic-safe source/dependency artifacts."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

root=Path(__file__).resolve().parent
target=root/'receipt-release-r1-private'
names=['attributed_text_candidate.py','messages_store_checkpoint.py','messages_attributed_receipt.py',
       'bounded_message_observer.py','await_message_receipt.py','message_receipt_journal.py',
       'receipt_chunk_coordinator.py','receipt_queue_handler.py','bounded_outbox_request.py','keyed_outbox_status.py',
       'test_full_receipt_queue.py','test_lost_outbox_reply.py','test_queue_deadline.py',
       'test_message_receipt_journal.py','test_keyed_outbox_status.py','test_messages_store_checkpoint.py',
       'attributed-fixtures-20261002.json']
for name in names:shutil.copyfile(root/name,target/name)
wheel='pytypedstream-0.1.0-py3-none-any.whl'
shutil.copyfile(root/'decoder-evaluation-private'/wheel,target/wheel)
for name,expected in [('original_daemon.py','f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'),
                      ('original_producer.py','382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f'),
                      (wheel,'499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278')]:
    assert hashlib.sha256((target/name).read_bytes()).hexdigest()==expected
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.iterdir()) if p.is_file()}
(target/'release-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2))
archive=root/'receipt-release-r1.zip'
assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(target.iterdir()):z.write(p,p.name)
print(json.dumps({'files':len(manifest),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'manifest_sha256':hashlib.sha256((target/'release-manifest.json').read_bytes()).hexdigest()}))
