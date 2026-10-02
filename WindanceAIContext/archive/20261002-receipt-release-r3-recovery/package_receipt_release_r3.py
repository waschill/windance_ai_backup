"""Fresh immutable package; never overwrites r1 or includes live message records."""
import hashlib,json,shutil,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
target=root/'receipt-release-r3-private';target.mkdir(exist_ok=False)
names=['attributed_text_candidate.py','messages_store_checkpoint.py','messages_attributed_receipt.py',
       'bounded_message_observer.py','await_message_receipt.py','message_receipt_journal.py',
       'receipt_chunk_coordinator.py','receipt_queue_handler.py','bounded_outbox_request.py',
       'outbox_request_guardian.py','receipt_request_worker.py','keyed_outbox_status.py',
       'bounded_outbox_status.py','keyed_outbox_admission.py','bounded_outbox_client.py',
       'receipt_outbox_dispatcher.py','outbox_wire_protocol.py','outbox_protocol_cli.py',
       'test_receiver_dispatcher.py','test_dispatcher_status.py','test_dispatcher_rotation.py',
       'test_dispatcher_queue_bound.py','test_persistent_receipt_flow.py','test_worker_legacy_contract.py',
       'test_outbox_client_parent_loss.py','test_worker_cli_composition.py','test_worker_cli_deadline.py','test_admission_worker_flow.py',
       'test_admission_crashes.py','test_bounded_admission.py','test_bounded_outbox_status.py',
       'test_status_wait_transition.py','test_process_local_deadlines.py','test_request_guardian_lifecycle.py',
       'test_worker_owner_boundary.py','test_message_receipt_journal.py','test_keyed_outbox_status.py',
       'attributed-fixtures-20261002.json']
for name in names:shutil.copyfile(root/name,target/name)
wheel='pytypedstream-0.1.0-py3-none-any.whl'
for name,expected in [('original_daemon.py','f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'),
                      ('original_producer.py','382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f'),
                      (wheel,'499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278')]:
    source=root/'receipt-release-r1-private'/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
    shutil.copyfile(source,target/name)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.iterdir())}
(target/'release-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2))
archive=root/'receipt-release-r3.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(target.iterdir()):z.write(p,p.name)
print(json.dumps({'files':len(manifest),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'manifest_sha256':hashlib.sha256((target/'release-manifest.json').read_bytes()).hexdigest()}))

