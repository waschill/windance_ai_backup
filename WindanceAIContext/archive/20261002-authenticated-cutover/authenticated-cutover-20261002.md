# Messages identity across authenticated cutover and rollback

October 2 UTC / October 1 Mountain 2026. Staged only; Phase 1 open.

The previous staged generic AUTH identifier would give a Messages retry a different manager key after switching from the installed SAL/Harness forwarding path. That could create duplicate work if acceptance happened before the old sender cursor advanced. No production path used that candidate.

The staged Messages adapter policy now explicitly selects the existing `max-imessage:` namespace. Intake accepts only a canonical positive decimal row ID in that namespace and retains it as the manager primary key. Other adapters retain issuer-derived generic IDs. The receipt helper requires the exact row identity it submitted, not merely a syntactically valid unrelated ID. Caller identity and source hash remain checked separately; an existing unattested record is never promoted to authenticated provenance automatically.

## Verified scope

Extended isolated integration executes the installed SAL run loop and the actual installed manager legacy `/messages` function alongside the staged authenticated handler, using a real loopback test server and disposable databases. New authenticated acceptance followed by retry through the installed legacy handler leaves one record. Old legacy acceptance followed by retry through authenticated intake returns409, leaves one old record and creates no provenance. No worker, sender or production database is started. The earlier two-owner/session/notify, lost acknowledgment, content-policy refusal and following-row tests still pass; the earlier authenticated source/fact test also passes.

This proves those handler identity contracts, not a complete rolling upgrade or rollback. The legacy route still lacks person authentication, even though it cannot alter an existing matching record through this handler. It must not be treated as a trusted memory source. The current source reader accepts only the authenticated provenance join. Downstream jobs/side effects, raw legacy callers, real cursor recovery, actual protected transport and natural sending remain outside this fixture.

## Deployment and recovery requirements

Before switching actual intake, coordinate ownership, pause only the relevant consumer outside protected constraints, verify no accepted-but-unacknowledged row is pending, and back up the manager and sender cursor/state. Inspect pending work rather than replaying it. A409 for an old row requires explicit reconciliation; never clear its ID, change the source namespace, rewind the cursor or fabricate provenance to bypass the hold. Rollback must preserve message rows, provenance and cursor history; restore source/config only under the recorded idle conditions. This packet itself changes no production source/config/schema/cursor and needs no production rollback.

Evidence includes current modules, extended integration tests and sanitized JSONL receipt. Private reproduction directory: `/Users/herald/services/source-memory-http-20261002`. Run `test_authenticated_sender_chain.py` and `test_authenticated_message_ingress.py` with its existing Harness Python environment. No live message, contact, credential or mailbox contents are included. Actual policy packaging/redaction, complete app wiring, protected transport, credentials and conversational memory still need completion before rollout.

Application model calls, dispatches and actual sends: zero. Codex work cost unknown. Odoo, SAM, SyncThing, disabled Level8, Warden suspension and phone state unchanged. Node-RED access remains independently held.
