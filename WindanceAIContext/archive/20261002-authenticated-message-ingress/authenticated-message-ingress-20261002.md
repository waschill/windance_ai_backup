# Authenticated adapter intake and memory source binding — staged

October 2 UTC / October 1 Mountain 2026. Phase 1 open; no production deployment.

Fresh inspection of the installed manager confirms `/messages` still accepts a caller owner field and defaults missing owner to William. Its installed source hash is recorded in the test receipt. A valid owner name is not authenticated person identity. The new module stages a separate authenticated intake handler, with an explicit adapter credential, allowed owner set and fixed channel. Source ID and text are the only other envelope inputs. Owner/session/channel/notification overrides cannot be smuggled through extra fields. The adapter must itself apply the installed SAL sender/direct-chat checks; possession of an adapter credential does not independently prove a human identity.

The manager message and authenticated source metadata are stored in one SQLite transaction using the actual installed manager schema. Stable issuer/channel/source identity determines the record ID. An identical retry returns its existing receipt; changed owner or text conflicts. Server chooses a per-owner/channel session. Notification is zero in this staged path; production integration must deliberately preserve the established sender-specific reply path and avoid duplicate acknowledgments. No production callers have been moved to this path.

An attested-source loader joins message and provenance, checks owner/channel/text hash and refuses legacy, missing, changed or mismatched records. It has no legacy fallback. It feeds the existing source-bound fact gateway; it must replace the unauthenticated manager source loader when this route is integrated. This does not seal off every old source-reader or write route yet.

## Evidence

`test_authenticated_message_ingress.py` extracts the actual installed manager init/schema function, executes it only with disposable storage, and serves the candidate through an aiohttp test server. No manager worker lifecycle, task dispatcher or sender is started. Tests cover invalid credential, owner outside the adapter scope, session/notification injection, required content-policy rejection, identical retry, conflicting source reuse, source/fact chain, cross-owner withholding, legacy-source rejection, changed-source rejection, and forced source-insert failure with atomic rollback. The final rerun passed. Forced SQLite failure initially returned a generic framework 500 with a traceback; candidate now catches storage failures and returns fixed 503 text without exception details, then passed again.

Content policy is a required server dependency, exercised with a synthetic rejection predicate. Integration still must use the actual installed privacy classifier and verify rejection before source persistence. This fixture is not evidence of comprehensive secret detection. Actual SAL sender mapping, real credential provisioning and protected transport are not tested by this synthetic adapter. A connection to the installed full manager app, existing sender-specific acknowledgment behavior, crash recovery across the actual transport and natural user acceptance remain open.

## Recovery and next work

Exact candidate, test, dependencies and sanitized receipt are archived with SHA-256 manifest. Private test location: `/Users/herald/services/source-memory-http-20261002`; run with `/Users/herald/.hermes/hermes-agent/venv/bin/python test_authenticated_message_ingress.py`. Production sources, schema, credentials, cursor and routes are unchanged; no production rollback is needed. Do not deploy merely because these isolation tests pass. Next integrate the actual sender adapter and source privacy classifier with authenticated transport, preserving its stable retry and fixed-recipient delivery contract, then connect conversational memory operations without a legacy bypass.

Zero application model calls, sends, task dispatches, Odoo writes or paid commitments. Codex work cost unmeasured. SAM, Warden suspension, SyncThing, disabled Level 8 and disabled phone remain unchanged. Node-RED remains separately blocked by browser policy and was not accessed through another route.
