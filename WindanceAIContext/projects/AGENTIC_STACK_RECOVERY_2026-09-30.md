# Windance baseline backup and recovery record

## October 1 owner direction and approved recovery — current override

William approved the coordinated training correction and unchanged Harness registration. He deferred Shawn's actual-training-note collection and pilot until after this project: keep collection suspended; it is not a current completion blocker. He authorized temporarily suspending Warden checks until project completion. Warden is paused and its two gui/501 jobs are unloaded; preserve its code, incidents and consensus policy and restore the recorded jobs/supervision at project completion after maintenance coordination. Do not rely on stale cached Warden status or older unanswered-approval passages below.

HERALD Harness was restored at 04:47 UTC October 1 with health 200 and unchanged task/delivery/run/revision ledgers. The four training fields and matching recipient helper are installed and structurally verified; a live read-only dated training response passed. No manual send, dispatch or SAM service interruption occurred. Natural delivery acceptance is still zero of seven. An unintended editor removal of SAM's cross-tab temperature-alarm notification wire was detected; gauge monitoring and SAM service remain intact, but that alarm notification path is disconnected. Its supported link-node restoration is staged and held for William's specific approval after automatic approval review rejected the import. Do not bypass that hold. Other service recovery and phase gates remain open.

Authoritative details, exact evidence and recovery instructions: `archive/20261001-approved-recovery/approved-recovery-20261001.md`. This dated override supersedes older pending-approval, note-pilot and Warden-active statements; it does not erase history or declare the project complete.

Companion to [the baseline](AGENTIC_STACK_BASELINE_2026-09-30.md). These are fresh, selective recovery artifacts, not complete machine images. Copying them into production is not an approved recovery plan by itself.

## Locations and coverage

Private off-host collection on HAL: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20260930T0600Z`. Its inherited ACL was replaced with access for the current owner and SYSTEM. Remote backup roots are mode 0700; copied source/data artifacts are mode 0600. Operational contents remain private and are not published with this report.

| Host | Fresh remote location | Verified content |
|---|---|---|
| HERALD | `/Users/herald/backups/agentic-baseline-20260930T0600Z` | 61 files: selected service/source/persona files, safe service definitions, manager project/stage/event export, selected Harness staff/review tables |
| HERALD supplement | `/Users/herald/backups/agentic-baseline-20260930T0607Z` | Five additional exact connector/report-history/sender source files; resolves initial incorrect guessed connector filenames |
| SAL | `/Users/zuzu/backups/agentic-baseline-20260930T0600Z` | 33 files: Node-RED flow/package metadata, selected producers/transports, Warden source and consistent incident DB, safe LaunchAgents |
| SAL supplement | `/Users/zuzu/backups/agentic-baseline-20260930T0607Z` | Ten additional sender/adapter/outcome/preference sources; resolves the nonexistent initial report-sender filename |
| SAM | `/home/williamschilling/backups/agentic-baseline-20260930T0600Z` | Nine files: app/kiosk/systemd files and consistent complete schedule SQLite |
| AL | `/home/waschilladmin/backups/agentic-baseline-20260930T0600Z` | Deployment metadata, image digests, mounts, ports, restart policies and selected nonsecret settings only |
| Canonical Git | Commit `42c5b6e2499316ac3b7874ced175b0216a9ef12c`; `current-control-plane/20260929-235534-pre-managed-upgrade` | Fresh existing sanitized backup workflow, confirmed on remote main; reason identifies audit, not an upgrade |
| HAL Git recovery | `canonical-context.bundle` and `isolated-context-repo` under the HAL collection | Complete canonical Git history at the restore-point commit; bundle verify, isolated clone and full fsck passed |

All 118 source/data artifacts from HERALD, SAL, SAM and supplements matched their manifests after transfer to HAL. AL's separately copied deployment inventory matched its manifest too. Each host retains its `MANIFEST.json`; sanitized copies and verification results are published under `archive/20260930-agentic-baseline/evidence`. Artifact SHA256 values are authoritative in those manifests, rather than repeated selectively in this guide.

## Database recovery scope

| Snapshot | Kind | Integrity and retained rows |
|---|---|---|
| HERALD `manager.db` | Selected-table export | Integrity ok; three projects, 24 stages, 98 events |
| HERALD `harness.db` | Selected-table export | Integrity ok; 36 staff tasks, 12 delivery records, 36 run records, three report reviews; empty retained notes/revisions |
| SAL `incidents.sqlite` | SQLite backup API | Integrity ok; 11 checks, one incident, four events, four notices, one budget row |
| SAM `sam_schedule.db` | SQLite backup API | Integrity ok; 75 schedule days, 4,243 schedule items, 3,853 events, 101 historical detail rows, 46 service-history receipts and 41 need-clear receipts |

SQLite reads used a pinned transaction and query-only source connections. Full copies used SQLite's WAL-aware backup API; selected exports contain only the listed tables and their table definitions. Manager messages/state and Harness conversations, mailbox references, credentials, permissions and general memories were not exported. Indexes/triggers outside the selected table definitions are not a reconstructed full schema. Never replace a live manager/Harness database with these partial exports.

## Restoration tests actually performed

1. Created new `isolation-restore` directories outside live service paths. Copied every selected file, recomputed SHA256 and parsed Python/JSON/plist where applicable. No application module was imported or started. All checked hashes and parsers passed.
2. Opened restored SQLite files read-only, checked integrity and exact snapshot row counts. All four copies passed. No restored queue or scheduler was loaded.
3. Queried the cold manager and Harness copies on HAL. Both delivered reports matched their hashes, Athena approved the same exact hashes, sender receipts were successful, and all 23 verified stages resolved to matching task-result hashes. This establishes recoverable evidence, not a new delivered outcome.
4. Queried the cold SAM copy. Historical details and service receipts survived; no detail completion was dated September 21 or later. No history was reposted to Odoo.
5. Parsed the copied Node-RED graph: 315 nodes, no dangling wire targets, old iMessage polling inject still disabled. It was never imported into Node-RED.
6. Reconstructed the fresh Hermes patch in an isolated Git index against `6d42313deee63b13dbf2f262d9a31cf603d3f1bc`. `gateway/authz_mixin.py`, `plugins/web/searxng/provider.py` and `gateway/windance_owner_guard.py` matched the live bytes. The production index/worktree was untouched. Receipt: `hermes-reconstruction.json`.
7. Verified the Git bundle, cloned it without checkout to the isolated HAL folder, and ran `git fsck --full` successfully. AL metadata was copied and JSON/hash validated without starting containers.

Isolation here was achieved by executing only file, parser and read-only database operations. It was not an application sandbox or boot test, and no network-capable restored service was run. Consequently cold data reconstruction passed; end-to-end application recovery, replacement-host boot, public authentication, physical kiosk/audio and delivery remain unverified. No full RTO was measured.

## Safe procedure for another cold recovery test

Use a new directory under the private recovery collection. Do not overwrite the retained copy or a service path. Compare its files with the relevant manifest; fail on any mismatch. Open database copies using SQLite URI `mode=ro&immutable=1`, then run `PRAGMA integrity_check` and compare the recorded table counts. For selected-table exports, run only the read-only evidence comparisons in the archived `verify_cold_recovery.py`, adjusting its fixed test-root path to the new private copy.

For the Hermes reconstruction, use a separate Git index or isolated checkout pinned to the recorded upstream commit, apply the recorded patch, add the owner-guard file and compare all three hashes. Do not execute Hermes, import restored plugins, or point a copied instance at production profiles. The archived `reconstruct_hermes.py` documents the exact successful method and fixed paths; inspect/adapt paths before repeating.

For a future application-level rehearsal, first create an environment with outbound networking denied, no production credentials, no mounted live databases, no production cursors/outboxes, and fake dispatch/delivery providers. Disable all RunAtLoad/KeepAlive/calendar/inject/native-cron activity in the test definitions before starting anything. The production definitions in this archive have not been converted into safe launchable test definitions. Merely changing ports is insufficient isolation.

## Production recovery requirements

A real repair requires a separate scoped execution decision based on current state. Record accepted work and uncertain sends first. Before service maintenance, pause Warden and wait for confirmed quiescence. If Warden proposes the repair, retain exact matching Codex and private Claude approvals; missing or disagreeing approval holds for William. A generic backup restore does not bypass that rule.

Selectively recover the affected source after comparing current hashes; provision omitted private configuration through its existing private channel. Keep the phone disabled. Reconcile task generations, in-flight operations, approval expiry, message ownership, report hashes, outbox claims and intake cursors before permitting dispatch or sending. Never replay saved run PIDs, cancelled stages, historical approvals, uncertain writes or uncertain deliveries. Do not restore the owner-deleted task backlog from older snapshots.

For manager/Harness evidence, recover missing records through a reviewed selective procedure that preserves newer data and the full current schema. For SAM, reconcile any post-snapshot local completion and Odoo history/clear receipts before considering a database replacement. For Warden, preserve current incident/review/execution reservations; never restore an older ungated repair engine or roll back history to force a retry. Independently verify affected services and permissions before resuming normal operation and Warden.

## Exclusions and remaining recovery gaps

No SSH private keys, API keys, OAuth grants, password stores, approval codes, `.env`, Node-RED credential store, Cloudflare tunnel secrets, counselor data, or private Claude transcripts were copied. The source/data guard rejects recognizable credential patterns; this is not a mathematical guarantee that arbitrary user prose contains no secret. Keep the private artifacts restricted and do not publish their contents.

Environment-bearing LaunchAgents were excluded in full, even when some values may be harmless. Sanitized live inventory preserves scheduling/executable metadata, but credentials and complete environment reconstruction still require existing private provisioning. Operational profile configs were inspected for model routes, not backed up in full. Messages DB, cursor/claim state, complete manager/Harness stores, AL volumes/image layers, bulk NAS/P content, Odoo SaaS exports, installed packages/model weights and private profile recovery were not covered.

HAL holds the off-host copies, but loss of HAL together with a source host remains a risk. NAS hosts answered SSH; no new NAS/off-site copy or replication verification is claimed. The published Git restore point is independent of the source services but intentionally contains only sanitized reconstruction material. A full disaster-recovery acceptance test remains outstanding.

## October1 00:35UTC selected HTTP application restoration
A fresh selected manager backup was restored inside a disposable AL container with network none, read-only inputs/root, no credentials or live volumes, bounded resources and worker lifecycle disabled. Two starts of the real HTTP handlers passed: three projects,24stages,98events preserved; status/owner/report-hash/delivery fields matched; zero upstream/worker/send attempts. Health correctly remained starting because workers were suppressed. Container exited0 and was removed; existing AL services remained up. This advances selected application recovery beyond cold parsing but does not prove full messages/state/credentials/worker recovery, native macOS parity, host boot or a complete RTO. Exact inputs, boundary receipts, repeat instructions and remaining limits: archive/20261001-manager-restoration/README.md. No production repair or phase advancement occurred; Warden's held Harness repair remains untouched.

## October2 WebUI application-data backup and isolated recovery verified

Production and lab application data captured privately on AL and copied to HAL. Each instance's three stable files/two SQLite databases passed off-host hashes, integrity and all-table comparisons; production upload reference captured. Network-disabled cached-image application ORM reads passed with temporary test key after initial missing-key failure. Original containers remain healthy and unchanged. Cache, production authentication/session recovery, image availability after host loss and complete host rebuild remain unproven; no interface acceptance or phase advancement claimed. Recovery record: archive/20261002-webui-recovery/webui-recovery-20261002.md. No inference, send, dispatch or production service changes. Phase1 open.

## October2 fresh SAM database backup and schema/cold recovery verified

Read-only online snapshot, pinned original/candidate schema functions and repeated initialization preserve all eleven existing tables/rows; candidate adds only empty intent table. Seven private files copied to HAL and independently hashed; four SQLite copies pass integrity and all-table comparisons. Service/two timers remain active with no restart, API, Odoo or model calls. No private rows/source published. Full startup, unknown-outcome reconciliation, need-clear concurrency and deployment gates remain; staged only, Phase1 open. Recovery instructions: archive/20261002-sam-existing-db-recovery/sam-existing-db-recovery-20261002.md.
