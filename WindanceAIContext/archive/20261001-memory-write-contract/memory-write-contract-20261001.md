# Learned-fact write contract audit — October 1

Current production Harness SHA256 remains db8a435907a2fb49796818a17b29334874b1919d6a03640901a22b6b12ea8195. No production change occurred.

The actual extracted upsert_memory function was run against a disposable SQLite fixture. Two different synthetic owner source strings using the same kind/key produced one row: the second overwrote the first. Both vector writes used the same source ID. Source strings do not provide ownership or authorization. This demonstrates a collision path, not historical disclosure.

Source inspection additionally found remember_text calls mirror_to_hermes_memory after the database write. That function appends to a shared configured MEMORY.md without owner/scope checks. Its error handler swallows mirror failures; remember_text still reports success. No real mirror contents were read or exported. The prior retrieval-only candidate cannot contain this independent copy path.

Eight direct writers were found: web research, explicit remembering, disabled-Level8 refusal recording, project workflow, weekly review workflow, daily reflection, SAM completion, and the direct memory endpoint. Level8 was only inspected as source; nothing was activated or tested. The direct endpoint trusts configured client IPs or bearer authorization, but has no fact-owner binding in this function. Background writers must be classified explicitly rather than assigned the current conversational identity by guesswork.

Next implementation contract: separate owned-fact storage keyed by owner, scope, kind and key; verified caller identity independent of request-supplied owner; durable source references and revision/correction history; transactional persistence plus readback before success; retrieval from current canonical facts; owner-aware derived copies or withholding when their access cannot be established. Business sharing requires explicit grants, not inference from a business-looking value. Preserve legacy rows without silently granting access or migrating their ownership. Reconcile reflection, SAM, direct endpoints and Hermes copies before deploying the staged reader. Test cross-owner equal-key isolation, correction/deletion propagation, mirror failures, missing identity, and background-source compatibility.

Evidence: audit_memory_write_contract.py and memory-write-contract-20261001.json. Zero model calls, sends, Odoo requests, service mutations or production memory writes. No deployment rollback is needed for this source audit. Phase 1 remains open.
