# Current report-and-sweep candidate recovery — October 2

Exact 21-source manifest d9dd9a97324d7ee1bbc5d1758a5670a78c54d35332cdaa8626fbc46bbf12e1ec now has fresh selected recovery evidence. Main61257141 includes the bounded sender-rule sweep; this supersedes older recovery certificates only for this staged revision. Production remains unchanged and candidate is not installed.

Fresh read-only online database snapshot and unchanged live source0a95a09f were captured at08:48:12UTC. Actual baseline and candidate startup used copied data/config/log paths with connections/dispatch denied. Health/static authenticated team200, missing-auth report401 and unconfigured-auth report503 passed. All28 original non-sequence tables were preserved and all baseline-startup tables matched; six new journal tables were empty and cold copy equal. HAL independently verified28 stable files, nested manifest/worker policy and four SQLite integrity checks at08:48:41UTC.

The restored release then passed five complete local-provider report cases (normal, lost mark-read, lost Trash, wrong account, missing policy), three complete local-provider sweep cases (normal and two lost responses), and the actual sweep HTTP/worker boundary suite. No uncertain write repeated on another report/sweep. HTTP suite verified401/401/503 prelaunch denial, actual empty worker200, injected timeout502, listing hold503, five malformed receipts and cross-owner prelaunch denial. Full nonempty tests used actual SDK/cache/transport/journal code; report classifier output was synthetic, sweep model calls forbidden. These tests do not establish real provider acceptance or natural scheduled delivery. Fixture listeners stopped; no production services restarted.

Private exact recovery locations:

- HERALD: /Users/herald/backups/email-sweep-release-recovery-20261002T084812Z
- HAL: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-sweep-release

Run verify_email_sweep_release.py against the HAL directory with the existing Second Brain Python to recheck hashes/integrity/table equality. Originals and database contents stay private. Restore into isolated new directories with outbound/scheduling/dispatch disabled, never over newer live data. The executable recovery script creates fresh copies and stops on source/manifest drift. No live rollback is needed. Actual restoration of an installed service would require fresh current backups and coordinated caller configuration; do not replay stored effects or approvals.

Remaining deployment gates: intended mailbox identity, explicit historical ownership reconciliation, coordinated authentication/caller transition (Node-RED access still blocked), broader entry-point/call bounds and actual provider/natural delivery evidence. Overall project and Phase1 remain open. SAM protected hours were respected; no SAM/Odoo/send/model action or paid commitment. Codex allowance cost remains separate and unpriced. Companion suite disclaimers refer to the scope of each fixture; this record establishes selected exact-package recovery, not a full-host rebuild.
