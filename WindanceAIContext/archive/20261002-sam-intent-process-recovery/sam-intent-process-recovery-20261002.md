# SAM history intent process recovery and competing attempts

October 2 UTC / October 1 Mountain 2026. Disposable child processes and synthetic effects only.

The staged journal was tested across real os._exit boundaries, not just raised exceptions. The remote effect is an fsynced line in a temporary fixture file; there is no HTTP/Odoo client in the test. Results:

- Exit after durable intent but before send: restart remains held; zero simulated creates.
- Exit after simulated acceptance but before journal confirmation: restart remains held; one simulated create, no second effect.
- Exit after confirmation commit: restart reuses the confirmed record ID; one simulated create total.
- Two separate processes competing for the same operation: first holds an in-flight reservation, second reports held without invoking its callback; first then completes, with one simulated create.

For each exit case a current consistent SQLite backup was copied to an independent directory, passed integrity_check and reopened in a fresh interpreter. Retry preserved its held/confirmed state and caused no new effect in the restored environment. All cases passed. The competing child was explicitly reaped; the fixture cleanup touches only its temporary directory.

## Operational meaning and remaining limits

The journal protects the tested duplicate-create window even across process death. It intentionally cannot distinguish a crash before send from a crash after unacknowledged remote acceptance, so both remain held. That conservatism must be visible to operations; it is not proof that the remote write happened or a reason to retry. No elapsed-time timeout, service restart or backup restore may erase the hold.

The test uses a snapshot containing the current intent state. An older backup that predates an attempted write still requires reconciliation before enabling writes. Power-loss/storage guarantees, remote Odoo behavior, full SAM startup/schema integration, legacy-receipt reconciliation, need-clear concurrency and an authoritative operator reconciliation path remain unverified or unfinished. This test does not authorize a live commit or modify any Odoo permission.

Before deployment, compose these checks with the actual SAM helper/application candidate, fresh verified backups, live maintenance ownership and protected hours. Preserve all old receipts and the new ledger together. Do not roll back to a writer that ignores outstanding unconfirmed intents, reset an intent, replay a real commit or fabricate a confirmed record ID to remove a hold. Production has no new journal table or changed writer yet.

## Reproduction and evidence

Archived exact `sam_history_intent.py`, `test_sam_intent_process_recovery.py` and sanitized result have SHA hashes. Private copies under `/tmp/` on SAM; run the test with its Python. It starts only its own bounded synthetic child processes and does not import the live SAM application. No production source/config/schema/service, schedule/history data or credentials changed. No rollback needed for this isolated work. Zero actual Odoo/API/model/send/dispatch calls or new charges; Codex cost unmeasured. SAM, Warden suspension, SyncThing, disabled Level8 and phone preserved; Node-RED hold unchanged. Phase1 open.
