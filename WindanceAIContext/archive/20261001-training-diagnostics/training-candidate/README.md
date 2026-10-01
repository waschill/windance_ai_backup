# Staged training delivery correction — October 1, 2026

Status: STAGED ONLY. Phase 1 remains open. No production code, recipients, schedules, memory, outbox or services changed. No seven-day delivery observation has started.

The saved training flow calls William's sender despite its Shawn label. The shared Shawn helper also depends on a removed formatting field. The candidate restores lookup from the existing private Shawn pin, rejects missing/invalid configuration or a William match, and switches only the training exec command to the existing Shawn adapter. It does not change Shawn's separate email-report SMS decision.

Three staged Node-RED function replacements require a successful deterministic training response with the current America/Denver date. Invalid source/status/date is withheld from delivery and the nightly memory snapshot. Snapshots explicitly describe planned work, never training progress. Delivery uses a stable owner/date key with the existing durable sender. Same-day changed content must hold for reconciliation, not silently send again.

## Evidence

- Six synthetic recipient tests passed on HAL, including missing pin, invalid values, owner mismatch protection and upstream recipient override. No real contact appears in these fixtures. Remote interpreter parity is not yet tested.
- Eight grouped JavaScript checks passed on HAL: current date, rejected source/status/stale data, UTC/Mountain boundary, stable key, shell argument isolation, invalid keys, snapshot meaning and narrow patch scope. Loaded Node-RED compatibility remains unverified.
- Six checks of the actual SAL sender's AST-extracted enqueue function passed in private temporary directories with real filesystem locks. Repeated triggers retained one identity; changed content was rejected; inflight and uncertain markers prevented requeue; retained receipts prevented requeue. A claim with no queue, receipt or uncertainty marker recreates the queue. This last behavior is an explicit recovery boundary, not proof against every crash window. No sender main, daemon, network or live outbox was accessed.
- The first SAL test failed because system Python evaluated newer type annotations; using deferred annotations corrected the isolated harness. It did not require changing production code.
- Read-only caller search found the shared resolver in ledger_unpaid_invoice_report.py and send_shawn_report_payload.py. Existing saved-flow hash remains the packet's precondition. Prior authenticated runtime readback returned HTTP401; saved configuration is not proof of loaded configuration.

## Use and recovery

Archive layout retains invoice-candidate recipient fixtures and training-candidate packet paths so the supplied tests can run from this archive root. test_sender_isolation.py is designed for SAL and reads only sender source plus its own temporary files. It does not execute the sender application.

Do not install this packet by overwriting flows.json. First obtain authorized authenticated runtime readback, compare current code and node hashes, inspect current maintenance/incident state, take and verify fresh backups of precisely affected private files and runtime configuration, and establish supported deployment/rollback. The shared resolver must be installed before the training command can use it. Review invoice callers together with the separately archived invoice candidate. Preserve recipient permissions, transport policy and outbox identity/claims/results. No replay or manual send is authorized by these tests. Preserve all Warden holds and SAM protected hours.

After any later authorized deployment, verify actual runtime bindings and observe natural deliveries with independent recipient/date receipts. Roll back only the changed functions/command from that deployment's verified backup if health fails; do not remove delivery claims or receipts. No production rollback is needed now because nothing was deployed.

Incremental installation/API charges: none incurred by these deterministic checks. Codex subscription usage and total project cost are not measured by this receipt.
