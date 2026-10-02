# Account-checked email candidate recovery — October 2

Exact 21-source candidate manifest dcfdd1100d28895db508edf4875b409a49687eed1e0599350c5212fef42967c5 now has isolated startup and selected restoration evidence. It remains uninstalled. This closes the older-revision recovery gap, not production acceptance.

Fresh read-only online SQLite backup and pinned unchanged live Harness source (0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0) were taken at 20261002T082039Z. Actual baseline and candidate module/ASGI startup used private copied data/config/log directories, blocked outbound connections and process dispatch. Health and authenticated static team reads returned 200; unauthenticated report returned 401 and unconfigured authentication returned 503. Startup audit was the only captured audit event. All 28 existing non-sequence tables were preserved; baseline startup tables matched candidate, six new journal tables were empty, and a cold copy matched.

HAL independently verified 28 stable files, the nested release manifest and worker policy, four SQLite integrity checks, original-table preservation and cold equality at 08:21:07 UTC. A subsequent run against the restored release exercised actual report/SDK/cache/transport/journal code with synthetic model output and a local fake Gmail provider: normal completion, lost mark-read response, lost Trash response, wrong account and missing policy all passed. Uncertain outcomes remained held on another report without another write. Wrong account made profile reads only; missing policy made no provider calls. Fixture listeners were stopped. No real provider/model call, send, Odoo action, SAM operation or service restart occurred.

## Private recovery locations and use

- HERALD: /Users/herald/backups/email-account-recovery-20261002T082039Z
- HAL: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-account

Run the accompanying verify_email_account_recovery.py with the HAL backup directory using the existing Second Brain Python. The 28-file manifest includes the release, unchanged original source and snapshot/baseline/candidate/cold databases. Scratch directories are not off-host recovery inputs. Private source and databases are deliberately excluded from the published packet.

Restore only into isolated directories with copied data, inactive scheduling and outbound/dispatch denial. Do not replace current live data with this snapshot or replay saved approvals/actions. A production deployment requires a new backup and coordinated maintenance; no rollback is needed for this test because production was unchanged.

Remaining gates: independently intended mailbox identity, historical ownership reconciliation and explicit migration, coordinated authentication across existing callers (including inaccessible Node-RED), actual provider acceptance and natural delivery. This is not full-machine disaster recovery. The workflow fixture's generic full-recovery disclaimer remains accurate for full-host dependencies; selected exact-package recovery is established here. No new charges were committed; deterministic tests used zero remote model calls, while Codex allowance usage is separate and unpriced here. Phase 1 remains open.
