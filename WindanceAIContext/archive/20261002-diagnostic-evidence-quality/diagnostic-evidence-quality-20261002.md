# Withhold unsupported diagnosis and repair — October 2, 2026 UTC

Staged correction, not production deployment or completion of the general diagnostic pilot.

An actual isolated-worker regression reproduced a reporting defect: contradictory effect evidence produced `insufficient_evidence` while still returning a concrete repair and rollback proposal. The previous worker did not strictly validate count types or source hash shape, and a missing field raised rather than returning an honest partial result.

The worker now requires the exact supported evidence schema, bounded string argument names, integer counts excluding booleans, valid distinct source hashes and the tested before/after effect relationship. Unsupported evidence yields no cause, repair or rollback recommendation. This validates evidence structure/consistency; it does not independently prove the source hashes correspond to real external facts.

Five actual isolated-container cases pass: supported evidence diagnoses the known mismatch; contradictory effects, missing field, boolean count and invalid source hash each return `insufficient_evidence` with all three recommendation fields null. The offline receipt inspector now accepts an honestly completed inspection with insufficient evidence and explicitly reports its diagnostic status separately from worker completion. It rejects insufficient results containing a cause or repair. Runtime completion is not a claim that a cause was established.

The predecessor failed the contradictory-evidence assertion; the accepted worker/inspector pair passed all five cases. Tests used disposable stages, read-only mounts, no network, fixed deadlines/resources, and removed their stopped containers. No real mailbox/source access or model call occurred. Missing JSON syntax, arbitrary source reasoning, oversized HTTP transport/streaming and further contradictory/corrupt records remain gates.

This changes `bounded_diagnosis_worker.py` and `inspect_diagnostic_record.py`. The previously consolidated recovery ZIP remains an exact historical restore point and does not certify this revision; do not silently use its old pins for the new worker. Canonical packet hashes identify the new pair. Full integration/package certification must use the new worker hash. Other current components are unchanged.

No production service/listener/scheduler, business send, Odoo or operational staff task changed. No SAM interruption, Warden restart, phone/Level8 or SyncThing change. Application model calls zero; no new charges. Latest account checkpoint remains78% used/22% remaining, not requeried. Project and original pilot remain open; no rollback required for production.
