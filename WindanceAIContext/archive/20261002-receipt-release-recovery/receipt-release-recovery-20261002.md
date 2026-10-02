# Staged receipt release r1 cold recovery — October 2

Exact20-file bundle contains10 staged runtime modules, six selected tests, synthetic Foundation fixture JSON, pinned original daemon/producer source and unmodified pytypedstream wheel with its bundled license/metadata. No credentials, real queue contents, mailbox bodies, recipient configuration or production databases included. This is recovery of a staged implementation/test package, not a full live outbox/host backup.

Archive SHA256 `99a0ea538b950eab903662e7271e4cc53c77ee23b218656f87fa43aa7690b61d`; release-manifest SHA256 `3d26953ca35a795bf05e3cad179c4c093f3ea36f11c2f03af01675c9b8024bab`. Manifest records every source/dependency hash; ZIP includes manifest as an additional file. Wheel499920d4 and original daemonf90fc54f/producer382b5512 verified before packaging. No installation.

## Locations and restoration

- HAL: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-receipt-release\receipt-release-r1.zip`; fresh extracted directory `restored` alongside it.
- SAL: `/Users/zuzu/backups/receipt-release-20261002-r1/receipt-release-r1.zip`; fresh extracted directory `restored` alongside it.

verify_receipt_release.py verifies expected ZIP digest, rejects duplicate/path-bearing members and oversize expansion, creates a new destination only, then verifies exact archive inventory and all20 hashes. Both hosts passed. Restore into a new isolated directory; never extract over a live service/outbox. No sender/scheduler activation is part of restoration.

## Restored execution evidence

From SAL's cold extracted copy, using original sources/wheel/fixtures within that same restored tree: full nine-case queue/main/owner-lock/receipt suite passed; both actual-producer lost-caller cases passed; normal and before/after-send timeout cases passed. Timeout measurements1.511/1.512seconds for the1.5-second fixture bound. All effects were intercepted synthetic SQLite rows, never Messages sends. HAL extracted copy passed journal concurrency/recovery/missing-history and ten keyed-status scenarios. Final post-test checks on both hosts verify all20 source hashes and unchanged archive. Python bytecode caches may appear outside the manifest; source/archive verification is unaffected.

## Remaining live recovery gate

Do not call this production-ready or a complete machine backup. A live rollout still requires a fresh coherent producer/daemon/configuration/queue/claims/results/inflight/uncertain/journal backup, restoration preserving post-snapshot uncertain effects, authenticated/bounded caller status integration, lifecycle cleanup and agreed deadlines/protocol coverage. Replaying an old queue snapshot can duplicate a real message; restored history must not be used to reset attempts. The full implementation still consists of staged modules/tests without a production entry point or installed caller changes.

Reproduction commands from SAL restored directory use python3 -B with test_full_receipt_queue.py, test_lost_outbox_reply.py and test_queue_deadline.py, passing local wheel, original_daemon.py, original_producer.py where required, and attributed-fixtures-20261002.json. See their argument order in included tests. No real send/model call or new paid commitment; Codex cost unknown. SAM/Odoo/SyncThing/Level8/Warden/phone/model routes and live services/schedules unchanged. Phase1 remains open, natural delivery gate unchanged.
