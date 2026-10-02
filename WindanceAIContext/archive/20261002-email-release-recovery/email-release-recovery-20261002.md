# Current email release — exact source and off-host recovery

October2. Fresh read-only snapshot and isolated restoration now cover current20-source-file release manifest1262ea18e24c244c75a63545afbbae8bab1485c82218f021c4f44029e591046e. Main5e95c9d6a11fcd5d685c81b942227423b3a67dc902beb10285bf206cf33449df. This supersedes earlier exact-revision recovery gaps for this package only; no live deployment.

At07:56:05UTC HERALD verified all staged source hashes and worker-policy manifest binding, verified unchanged live main0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0, and took a fresh read-only online SQLite backup. Private package: /Users/herald/backups/email-release-recovery-20261002T075605Z. Its release subdirectory uses actual service filenames; original source, snapshot, baseline-started, candidate-started and cold database copies are retained privately. The stable private manifest covers27 files; test scratch directories are not part of the exported recovery set.

Actual original/candidate module import and ASGI lifespan ran against separate copied databases/config/log paths with network connects and subprocess/dispatch denied and audit intercepted. Health and authenticated static roster returned200. Candidate report with missing authorization returned401 and absent configured auth returned503 without worker launch. All28 original non-sequence tables are unchanged; every original table matches baseline startup, including sequence behavior. Six added recovery tables are empty; cold-copy tables match. This startup test does not run a real mail report or model.

HAL private recovery location: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-release. Only the release directory and stable private files were copied. Independent verification at07:56:48UTC passed all27 file hashes, nested release manifest, worker policy, four SQLite integrity checks, original-table comparisons and empty new recovery tables. No private database rows, source bundle or account material is published here.

## Selective restoration instructions

1. Retain both private packages and preserve current production state. Run verify_email_release_recovery.py with the exact HAL directory to recheck hashes and immutable SQLite copies; it emits metadata only.
2. For isolated startup, inspect recover_email_release.py. Copy the selected database into fresh scratch data/config/log directories, use the verified release's agent_harness.py and helper paths, deny all external connects/subprocesses, intercept startup audit and keep authentication configured to a synthetic test value. Never start production schedulers, senders or task dispatch as part of recovery.
3. Compare original table contents against the baseline-started copy and check new journals before using a restore candidate. Preserve every current uncertain/confirmed action record. Do not overwrite the live database with this snapshot: provider effects can outlive it. Actual production rollback/reconciliation must be coordinated against current state and backups.

## Remaining limits

This verifies selective source/database restoration on existing runtimes, not full replacement-host dependencies, account authentication, actual provider acceptance or natural scheduled delivery. Real caller identity remains unresolved. Shared-token rollout affects66 routes; existing callers, including the inaccessible Node-RED path, need coordinated verification before any global token change. Immutable code-loading/race resistance and other direct email entry points remain open. No installation is authorized by this evidence alone beyond existing owner scope/gates.

No service interruption, mail/model/Odoo/SAM action, schedule, Warden, SyncThing, Level8, phone or routing change. Existing software, zero application model calls and no paid commitment; Codex usage and dollar attribution remain separate. Phase1 open.
