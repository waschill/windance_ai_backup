# Actual outbox crash and duplicate-prevention tests

Read-only production source extraction; disposable directories and synthetic payloads only. No real send or production queue/cursor mutation.

Current send_imessage_payload.py SHA256:382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f. Current imessage_outbox_daemon.py SHA256:f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009.

Six scenarios using the actual enqueue/handle/atomic_json/hold_uncertain functions passed: completed retry, crash after intercepted send, crash after retained receipt publication, changed-content key conflict, recovery before queue publication, and failure partway through a multi-chunk message. Completed or uncertain work was not resent. Uncertain cases retained a negative receipt and quarantined payload for reconciliation. Claim-only pre-queue recovery republished unsent work. send_one was replaced with an intercepted counter; this test never invokes Messages, osascript or the production daemon.

The first extracted-function run failed before any test operation because SAL Python required the original postponed-annotations behavior. The fixture compiler now explicitly preserves that flag; all six scenarios passed on rerun. No production Python/runtime modification was made.

The actual staged bridge-function harness was extended with a cursor-save failure after a successful intercepted sender return. All four scenarios passed. The failed final row kept the preceding cursor, and the retry preserved the same request and acknowledgment IDs. Combined with the outbox component tests this establishes the relevant stable-key and retained-result contracts, not a full process-level bridge/manager/sender crash test.

Private allowlist structure was checked locally on SAL without exporting entries: two keys, both unchanged by the stricter phone parser; both mapped owner names normalize to supported William/Shawn identities. No allowlist edit or new recipient enrollment occurred.

Important limit: the daemon's successful receipt follows send_one returning from osascript; it does not independently verify Messages sent/delivered flags. Thus this evidence does not close the earlier error-notification delivery gap or training natural-delivery pilot. Never translate process success into confirmed transport delivery. Crash simulation, rather than terminating a production process, was used. Source configuration and queue owner locking remain separate production checks before deployment.

Candidate sender boundary remains staged. Next perform fresh backup, live ownership/in-flight checks and controlled deployment of the narrowly tested intake boundary if predicates hold; no cursor rewind or old-message replay. Authenticated person propagation and full memory integration remain separate unfinished work. Phase1 open; zero model calls, Odoo requests or external messages.

Evidence: test_outbox_crash_contract.py, test_actual_sender_bridge.py, outbox-crash-contract-20261002.json, actual-sender-bridge-crash-20261002.json.
