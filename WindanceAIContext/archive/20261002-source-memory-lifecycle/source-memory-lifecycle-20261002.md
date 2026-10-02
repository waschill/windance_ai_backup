# Source-bound correction and forgetting — staged evidence

October 2 UTC / October 1 Mountain 2026. Production remains unchanged; Phase 1 remains open.

The staged source-memory HTTP router now supports correction and forgetting through `/memory/owned/change-from-message`. A scoped credential is checked before retrieving the retained owner message. That message must explicitly identify the same memory record and operation as the request. Corrections obtain their replacement value from the retained source, not caller-supplied free text. The expected current revision prevents stale requests from overwriting newer changes. The fact, request receipt and source provenance commit together.

Actual current Harness app HTTP tests ran in disposable data/config/log directories with synthetic credentials and sources, intercepted outbound operations and no production schema changes. The lifecycle test passed again during this continuation. It covers initial capture, correction, forgetting, wrong target, stale revision, negative forgetting wording, cross-owner withholding, source drift, quoted instructions, secret fixtures and conflicting caller overrides. Replaying a forgotten request returns already_recorded; replaying an older correction returns superseded and does not resurrect the forgotten fact. The response explicitly says source messages remain retained. Earlier component regression evidence records 47 passing cases; this continuation re-ran the actual HTTP lifecycle only.

## Acceptance limits and next integration

The explicit 32-character record identifier syntax is a backend contract, not acceptance of a usable conversational assistant. Natural target selection must present the identified fact and revision, resolve ambiguity without guessing, and bind the resulting action to an authenticated retained owner request. The current manager owner field alone does not authenticate a person. Real adapter credentials, transport and source provenance remain deployment gates. No live route was mounted, no real credentials provisioned, and no production source was read by these tests.

Legacy readers, writers, mirrors and derived memories still need coherent integration; generic write routes must not bypass this source-intent path. Shared-source privacy, inferred habits and correction propagation remain unfinished. Forgetting clears the selected current fact, not retained conversations, source history or older backups. A restored older snapshot requires post-backup reconciliation before serving memory. Source validation is not a distributed transaction with its source database and does not establish external truth.

## Reproduction and recovery

Private test directory: `/Users/herald/services/source-memory-http-20261002`. Run its `test_source_memory_http.py` with `/Users/herald/.hermes/hermes-agent/venv/bin/python`; it mounts the staged router only in its disposable process. The archive includes the exact router, source/gateway/store/policy dependencies, test and sanitized receipt, with SHA-256 manifest. The current installed Harness source is not replaced. No production rollback is required for this staged work; do not install an older complete Harness candidate over newer deployed privacy/invoice guards.

Application model calls and sends: zero. Codex work cost is unmeasured. No SAM interruption, Odoo write, service restart, SyncThing change, Level 8 action, Warden activation or phone activation occurred.
