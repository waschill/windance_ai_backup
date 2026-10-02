# Exact cached-email candidate recovery verified

October2, 2026. This extends recovery evidence to the current private candidate61028799755ebc22d823a56da155adf0489cdceefb1669ac973c25a97df2ef93, not just its predecessor. Phase1 remains open; nothing was deployed.

At07:01:37UTC HERALD took a fresh read-only online database backup and copied the exact12-file candidate and unchanged production source. Private recovery package: /Users/herald/backups/email-cached-transport-recovery-20261002T070137Z. Live source hash remained0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0.

Actual full baseline and candidate import and ASGI lifecycle passed in isolated directories with socket connections, subprocesses, model, mailbox and dispatch effects denied and audit intercepted. Health returned200. Existing sweep authentication/held/error responses returned401/503/502. All28 original non-sequence tables were unchanged; all original tables matched baseline startup. Six added recovery tables were empty; the intent-state index was checked. Cold copy and repeated table comparisons passed.

HAL independently verified17 stable manifest files and four SQLite integrity checks at07:02:14UTC. Off-host private package: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-cached-package. Snapshot SHA256348328a17a55a797c88415f77000c63c292408a3bfefa8d332699ffdf1e64ba5. Candidate/cold database SHA256d7b3b30fb3595aa65d6a72ea194277b6d34e2b5e29ba50a5b7cbfb9787fedc66. Transport5753b6c3b9ac59021b2de6480656d167502d550e61254633aff09e4197a05c12 and private auth-cache helper2c50a126b771a12cae668d74de3bdf3dd969fe29134329ae6d9fb1cb42440803 match the intended source revision.

## Recovery instructions

Run verify_email_offhost_recovery.py with the exact HAL package path and --cached-package to verify immutable files, integrity and all tables without outputting private rows. To repeat startup restoration, inspect test_email_cached_recovery.py: it explicitly checks exact source hashes and redirects data/config/log paths, denies external effects, intercepts startup audit and prevents dispatch. Preserve these constraints. Do not use a prior database snapshot to replace live state or clear uncertain action journals. Remote provider effects may have occurred after any snapshot. Production rollback is unnecessary because deployment has not occurred.

## Remaining acceptance and cost

This startup test substitutes Gmail with deterministic failing fixtures; real credential/account identity and end-to-end production provider behavior are not certified. Separate loopback tests cover the candidate draft/journal/cache/HTTP path and lost acknowledgments. Whole-job time bounds, response decoding limits, privileged writers and real mailbox ownership remain open before installation. No phone, Odoo, SAM, Warden, Level8, SyncThing, schedule or send changed. Zero application model calls and no new paid commitments; Codex usage is separate and dollar attribution unknown. Private source and database are retained only in restricted recovery packages, not this published archive.
