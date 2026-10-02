# Full SAM r5 startup and selective restoration verified in isolation

Private candidate main 1e6a553a34ed27b6d1f51cba00d3c473843fee4f351e581cf4ac7282a8ffbdcf and all eight manifest files were copied from HAL into a new private AL test directory and verified before import. Database input is the earlier verified off-host snapshot, SHA-256 19223b6adb07b25ba91dca206a65507a310e808a7bf0a66c52ae44020b105f66, captured at 20261002T024254Z. This run did not create a fresh backup of current live SAM state; it proves this saved snapshot restores into the current staged candidate.

## Isolation and observations

Existing pinned image sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f was used without installation or download. Before start, Docker inspect verified network none, read-only root and evidence mount, nonroot UID/GID1000, all capabilities dropped, no-new-privileges, and a 45-second independent process deadline. Limits were 256MiB memory, 0.5 CPU, 64 PIDs and 64MiB temporary filesystem. No host port, Docker socket, live SAM volume or credential store was mounted. The Python test verified only loopback was present.

The full candidate module imported and actual main executed with documented home/data/database/assets settings redirected to temporary storage. Startup fetch_schedule, both weather fetchers and scheduler_loop were replaced before main with inactive recording callbacks. Actual schema initialization, handlers, HTML generation and read APIs were retained. Health, root, admin, schedule and trainers routes all returned HTTP200 with expected response shapes. Response bodies and private database values were not retained in output.

All 11 original tables/rows matched the saved snapshot. Only five empty recovery tables were added: sam_history_intents, sam_clear_intents, sam_memory_requests, sam_commit_snapshots and sam_rollover_receipts. A closed-database cold copy matched all table contents and passed another actual init_db call without change. The HTTP listener stopped and its thread joined; temporary database files were removed. Exact container e76278faa5d927076b83c8b4ed4d9fa9a52781164bf162452aada7ce965ee205 exited0 and was removed after inspection.

AL production containers were observed running before the test, with WebUI healthy. No production service was restarted, no SAM command was executed, and no external Odoo/memory/model/send/task action or scheduler body ran. SAM's protected interval was respected. Detailed-note collection, Warden suspension, phone/Level8 disablement and SyncThing were unchanged.

## Recovery locations and limits

HAL original eight-file candidate: project workspace sam-memory-r5-private. Verified snapshot: C:/Users/wasch/Documents/WindanceBaselineRecovery/20261002-sam-existing-db/sam-existing-db-recovery-20261002T024254Z/snapshot.private.db. AL private test copies remain at /tmp/windance-sam-r5-recovery-20261002 with owner-only parent access; /tmp is volatile and is not a durable backup destination. Shared packet excludes private full source and database.

Reproduction requires the pinned image, matching private stage and snapshot, the container constraints above and test_sam_startup_r5_container.py mounted under /evidence. Never run candidate main against a live database or enable producer/scheduler bodies to reproduce this test. No production rollback is necessary because nothing was installed.

This proves selective saved-database compatibility, full-module startup and five local HTTP reads under isolation. It does not prove visual browser rendering, actual scheduling, live integration, OS reboot, whole-host disaster recovery, changed-input correction or deployment readiness. The first-clear Odoo Boolean race and real dedicated producer credentials/TLS remain unresolved. Application model/API cost was zero; Codex usage is separate and attributable project dollars remain unknown. Phase1 remains open.
