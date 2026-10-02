# Actual sender loop to authenticated intake — isolated integration

October 2 UTC / October 1 Mountain 2026. Staged only; Phase 1 remains open.

Fresh installed-source inspection confirms SAL's bridge asks Harness for a durable receipt, sends an immediate acknowledgment through its existing row-based idempotency key, and advances its cursor only after that sender returns. Harness forwards to manager with notify=true; manager owns the later answer. A replacement must preserve both stages, separate owners, stable retry IDs and existing owner sessions.

The staged `authenticated_messages_adapter.py` sends a scoped bearer envelope with the mapped owner, stable Messages row ID and message. It requires HTTPS or literal loopback HTTP, rejecting plaintext remote HTTP and credential-bearing URLs. This URL check does not prove a tunnel, TLS trust, destination ownership or adapter secret provisioning. Those remain deployment gates. The helper validates the manager's accepted ID/source receipt before returning the same immediate acknowledgment. It never sends Messages itself.

The intake candidate now chooses notify from server adapter policy, never from caller fields, and preserves the installed manager owner session names (`william` and `shawn`). Its prior channel-suffixed staged sessions were changed before deployment to preserve conversation continuity. Isolated tests configure follow-up notifications true but never start a manager worker or sender.

`test_authenticated_sender_chain.py` uses a freshly extracted installed SAL run loop, the actual current manager init/schema, actual Harness remember parser/secret classifier functions, a real loopback aiohttp server and disposable storage. It supplies synthetic sender mapping/direct-chat results and an intercepted idempotent outbox. A lost sender acknowledgment caused the same source to be retried: two accepted input rows produced two manager messages, not three. William/Shawn sessions and notify policy were preserved, and an unverified group fixture was skipped. Actual database query/sender identity extraction and actual Messages delivery are not re-proven by this test; their earlier evidence remains separate.

Installed classifier checks, combined with the staged source-intent grammar, rejected ordinary remember, Vega-addressed business remember and exact-ID correction secret fixtures before source storage. This expanded grammar currently lives in the test integration and must be packaged with the production boundary; it is not installed. Keyword checks are not comprehensive secret detection. Control-code redaction and all actual caller compatibility still require reconciliation before bypassing Harness forwarding.

The existing loop retries HTTP errors, so a generic content-policy422 would indefinitely block its cursor. Intake now returns an exact content-free rejection receipt. The helper recognizes only that receipt, returns a fixed refusal acknowledgment, and the existing loop advances only after its sender acknowledges. The test proves the following normal row is accepted. Other auth, storage, malformed or uncertain failures remain retry failures; no automatic cursor skip. Final sender-chain and earlier authenticated-intake tests both pass.

## Recovery, evidence and remaining gates

No production source, schema, credential, route, cursor or service was changed. Exact staged modules, installed run-loop slice, tests and sanitized results are archived with hashes. Private test location is `/Users/herald/services/source-memory-http-20261002`. Reproduce with that environment's Python and `test_authenticated_sender_chain.py`, then `test_authenticated_message_ingress.py`. No production rollback is needed.

Still required: production policy packaging, actual adapter candidate/full-app integration, protected transport and credential provisioning, existing-message ID reconciliation at cutover (new AUTH IDs must not duplicate previously accepted legacy IDs), fresh backups and rollback, legacy identity-path containment, memory command dispatch/retrieval integration and natural acceptance. A successful fixture is not authorization to replay real messages or start a second consumer. No migration/retirement or phase closure is claimed.

Zero application model calls, external sends, dispatches or Odoo writes. Codex work cost unknown. SAM, SyncThing, disabled Level 8, Warden suspension and disabled phone preserved. Node-RED restriction remains untouched.
