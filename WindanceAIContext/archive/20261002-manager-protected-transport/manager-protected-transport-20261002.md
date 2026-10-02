# SAL to HERALD protected manager transport probe

October 2 UTC / October 1 Mountain 2026. Read-only live transport evidence; no intake cutover.

SAL successfully created a temporary SSH forward from literal loopback127.0.0.1:18797 to HERALD loopback127.0.0.1:8797 using its existing `HERALD` SSH alias. BatchMode and StrictHostKeyChecking were explicitly enabled, forwarding startup failures were fatal, and no multiplexed control connection was reused. A GET /health returned HTTP200 and service `vega-manager` while the owned SSH process remained live. The probe terminated only its own process and verified that its local port was closed afterward. No service was restarted or persistent tunnel registered.

The first probe addressed `herald@192.168.36.21` directly and failed SSH authentication, before manager access. Read-only inspection of selected SSH configuration fields showed that the existing HERALD alias selects the configured identity file whereas the direct address uses default identity selection. Using that existing alias succeeded; no key contents were read, exported, generated or installed, and no SSH configuration or known-hosts entry changed. Initial failure and final success receipts are retained separately.

## Scope and limits

This establishes an available encrypted, host-key-checked transport route for the planned authenticated adapter. It does not provision the adapter bearer credential, authenticate the upstream human, validate a persistent tunnel after reboot or prove end-to-end memory/delivery. Loopback access still needs the application's scoped credential. The staged endpoint must not silently fall back to plaintext LAN transport if its protected route fails. Persistent ownership, restart behavior and fresh backup/rollback remain necessary before configuring live intake to use it.

The health response exposes `status` and `service`, not an `ok` field; the receipt's null health_ok is a missing field, not a failed boolean or a claim of complete application health. The evidence is HTTP200, correct service identity, live owned tunnel and verified cleanup. Project queue contents, private messages and credentials were not printed. No POST, task dispatch, model inference or external send occurred.

## Reproduction and recovery

Exact probe archived as `probe_manager_protected_transport.py`. Private SAL copy: `/Users/zuzu/backups/probe_manager_protected_transport_20261002.py`. Run with `/usr/bin/python3` from SAL; it checks that the chosen loopback port is free, creates one bounded child, reads only manager health, then terminates/reaps that child. It exits nonzero if HTTP health or cleanup fails. Do not replace strict host checking with accept-new/no to force success. No persistent recovery action is required for this completed probe.

Application model calls/sends/dispatches and paid commitments: zero. Codex work cost unknown. SAM, Odoo, SyncThing, disabled Level8, Warden suspension and disabled phone unchanged. This accessed manager port8797 only; it did not access Node-RED or work around the separate browser denial. Phase1 and live conversational memory gates remain open.
