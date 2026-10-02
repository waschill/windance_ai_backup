# Preserve installed redaction before authenticated source retention

October 2 UTC / October 1 Mountain 2026. Staged only; Phase1 open.

Fresh source inspection confirmed current Harness forwarding applies `redact_level8_code`, then `redact_approval_auth_word`, before sending retained text to the manager. The staged direct intake previously lacked that transformation. It must not replace forwarding without preserving it.

The private full-manager candidate now packages the exact installed parser, secret classifier and both redaction functions. Its app factory supplies a required sanitizer to configured authenticated intake. Ordinary accepted text is sanitized before deriving the retained-source digest or inserting the manager message; source evidence therefore describes the sanitized source representation, not the raw original message. Raw control values are not copied into source hashes or receipts. Explicit remember/correction requests that require redaction are rejected before storage instead of silently recording changed factual meaning. Existing secret-like memory rejection remains.

## Evidence and limits

The full staged manager HTTP test uses actual middleware/routes, disposable databases, synthetic configuration and a substituted fixture Harness token; background workers are explicitly disabled. Synthetic approval-shaped and shutdown-code-shaped text yielded sanitized retained messages with no synthetic control marker. A memory command containing an approval-shaped credential returned422 with no stored message. Earlier authentication, retry, source-reader and unsafe/malformed-config checks still passed. Candidate source hash and frozen-policy hash are in the receipt.

These are string transformation tests only. No shutdown handler, Level8 executor, approval action, model, worker or sender was invoked. No real code, password or approval word was read or used. Installed redaction is pattern-based: it does not establish comprehensive secret detection, does not necessarily catch an isolated unlabelled credential, and must not be represented as globally sanitizing all private content. No historical leak is established by these synthetic tests.

The source representation change must be respected by future retrieval and receipts. It is not a basis to reconstruct or retain redacted originals. Old-ID cutover must compare the same sanitized representation as the installed forwarding path; no automatic promotion of old unattested records is permitted. Broader legacy identity-path containment and actual memory command routing/readers/mirrors remain unfinished.

## Recovery and next step

No production sources, schema, routes, credentials, cursor or jobs changed; no production rollback needed. Private candidate remains `/Users/herald/services/source-memory-http-20261002/manager-authenticated-candidate.private.py`. Reproduce with `build_manager_authenticated_candidate.py` and `test_full_manager_authenticated.py` using the existing Harness Python in that directory. Archived exact modules/tests/policy and sanitized receipt have a SHA manifest. The full source remains private.

Next wire deterministic learning/correction/forgetting and source-aware retrieval into authenticated conversations, preventing memory requests from falling through into legacy unrestricted writers or shared mirrors. Complete protected transport supervision/credentials and fresh recovery/maintenance gates before live intake cutover. Source-backed memory acceptance remains incomplete.

Zero application model calls, sends, task dispatches, Odoo writes or paid commitments. Codex work cost unknown. SAM, Warden suspension, SyncThing, disabled Level8 and phone unchanged. Node-RED remains separately access-blocked.
