# Exact bounded-history candidate startup and off-host recovery

Verified October 2 2026 at 03:42–03:43 UTC. Staged only; Phase 1 remains open.

Pinned candidate `2bfa3678156f7ee5d38eac01bf9e14e98d2370121d420a78fe65c2e624b2eb4f` passed full module import, actual ASGI lifecycle and health200 on a fresh private SQLite snapshot. The unchanged installed baseline was started against a separate copy for comparison. External socket connections and subprocess execution were denied; Gmail/model/staff adapters were forbidden and lifecycle audit intercepted. No production service was started or restarted.

All28 non-sequence tables match the snapshot; all original tables including sequence match baseline startup. The two added recovery tables are empty. The actual schema creates the state index and EXPLAIN selects its covering index for unresolved-count lookup. Cold backup matches every candidate table. Live source was still the pinned classification-guard revision when this test began.

Accepted private recovery directory: `/Users/herald/backups/email-private-recovery-20261002T034244Z`.
Independent HAL copy: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-bounded-history`.
Eight stable file hashes verified; all four databases independently pass integrity/table comparisons on HAL with immutable read-only connections. Backup file hashes remain unchanged after inspection. Manifest stays private with the package; no private source, rows, mailbox data or credentials are published.

Reproduce the off-host check with the archived verifier and HAL copy path as its positional argument. Use existing HAL Second Brain Python. For startup reproduction, the archived test pins exact source hashes, creates a fresh private snapshot and disposable application copies, and denies external effects. Retain historical packages, but do not use their older source hashes to certify a new revision.

Recovery is selective and isolated: never replace live databases over newer accepted operations, enable sending/scheduling/dispatch during restoration, or roll back to a writer ignoring outstanding intents. The test does not exercise actual Google credentials, real TCP serving, background worker ownership, mailbox marker preservation, requester/account binding, cross-path admission or old-snapshot reconciliation. Those remain gates; this is not production acceptance or full host disaster recovery.

No application model calls, mailbox actions, Odoo calls, SAM interruption, Warden restart, phone activation or model-route changes occurred. Codex capacity is consumed; attributable dollar cost remains unmeasured. Continue email integration while the separate approved Node-RED repair awaits permitted browser access.
