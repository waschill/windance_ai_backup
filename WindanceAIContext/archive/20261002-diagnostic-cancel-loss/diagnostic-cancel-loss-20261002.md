# Lost cancellation acknowledgment recovery — October 2, 2026 UTC

Staged isolated test; no production deployment. Original diagnostic pilot and complete job contract remain open.

The exact-container cancellation helper now saves a job/evidence/worker/container-bound stop receipt only after observing the worker stopped with exit137. It fsyncs the temporary receipt and atomically replaces the saved path before returning. A later identical call validates the existing input hashes and saved identity/receipt, then returns it without any Docker call or second kill. This is trusted local evidence, not tamper-resistant attestation.

Actual HTTP-to-AL cancellation test injected loss after the real helper successfully stopped its worker and returned a receipt. The API correctly stayed cancellation-pending. A second authenticated cancel call recovered an identical saved receipt and committed cancelled state. Result remained unavailable and the job could not be reclaimed. Exact job `0e5c4f64baef42d398ed569cb129d8a1`; sanitized output included. Test listener and launcher stopped, and the exact disposable container was removed. One synthetic worker ran; no business workflow was invoked.

The injected loss is after the remote helper's successful return, not an actual network outage. The gap between kill and receipt persistence, two concurrent cancellation callers, directory fsync/host power loss, and old/missing/changed receipt recovery remain unproven. A stopped worker without a valid saved receipt still requires explicit reconciliation; no automatic inference or repeated kill is authorized. Saved receipts are returned as historical stop evidence, not a new live-process observation.

Production services/schedules, mailbox/Odoo, SAM, Warden, SyncThing, Level8 and phone state unchanged. No application model calls or paid installation. No rollback required; preserve evidence and never reset an uncertain claim merely to rerun it. Canonical source/test/results are durable; temporary runtime directories are not production deployment storage. Prior account checkpoint remains78% weekly used/22% remaining; not requeried or reset in this run.
