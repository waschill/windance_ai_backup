# Current email candidate startup and off-host recovery verified

Fresh read-only inspection verified live Harness source 0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0 and all ten staged files in /Users/herald/backups/email-action-route-20261002. Candidate main is 4600e59f380d1de53e42fff2535e9865eb4e2b97dc1739313a6291e4c37c54b7. This record replaces reliance on the older undo-only candidate's recovery test; that historical test remains valid for its own revision.

At 20261002T062735Z, a read-only SQLite source connection produced a consistent new private online backup. Live source, candidate and nine helpers were copied into /Users/herald/backups/email-route-private-recovery-20261002T062735Z. Baseline and candidate were imported separately with data/log/config/Google configuration redirected to scratch directories. A Python audit hook denied socket connects and subprocess/system/spawn operations; mailbox/model/dispatch entry points were additionally denied. Actual ASGI lifespan and health ran, with audit output intercepted. No listener, Gmail credentials, background task or external service was exercised.

Both startup variants returned health HTTP200. All 28 existing non-sequence table contents were preserved; all original tables, including sequence behavior, matched the baseline startup. Six new recovery tables remained empty. The intent-state covering index was verified. Candidate database cold copy had identical table evidence and passed integrity checks.

All 15 stable files and the private manifest were copied to C:/Users/wasch/Documents/WindanceBaselineRecovery/20261002-email-route-package on HAL. Independent read-only verification at 2026-10-02T06:28:08Z matched every file hash, passed integrity on snapshot/baseline/candidate/cold databases, confirmed all table comparisons and rechecked unchanged backup hashes. Private source, DB rows, mailbox information and credentials are excluded from this shared packet.

## Selective recovery

The private manifest binds original/candidate sources, nine helpers and four database snapshots. Preserve it with the package. verify_email_offhost_recovery.py PATH --undo-package verifies this 15-file/six-new-table layout; the flag name is historical, and the candidate hash above is authoritative. test_email_route_private_recovery.py reproduces the private startup exercise on HERALD with pinned source guards and fresh output directory. It must not be repurposed to start workers or make mailbox calls.

Production rollback is unnecessary because no candidate was installed. Do not overwrite the live database from this snapshot during ordinary rollback: work may have occurred since backup. Any eventual data restoration requires maintenance coordination and reconciliation of newer tasks, approvals, intents and uncertain provider effects; old code that ignores pending intents is not a safe rollback merely because it starts.

## Remaining gates

Exact current source/database compatibility and selective off-host restoration are now supported. Real Gmail transport/account verification, intended human identity, uncertainty resolution, cancellation/time limits, sustained behavior and deployment remain unverified or incomplete. This was Python-level effect denial, not an OS network sandbox or full-host recovery. No real email report/action/send/model call occurred; no service was restarted and SAM was untouched. Application model spend was zero; project-attributable Codex dollars remain unknown. Phase1 remains open.
