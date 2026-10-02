# Exact diagnostic input and terminal records — October 2, 2026 UTC

Phase 1 and the original bounded diagnostic pilot remain open. This extends isolated prototype controls and does not deploy a job service.

Revision3 copies the fixed worker and sanitized failure fixture into a job-specific input directory before Docker creation. Each file is at most64KiB, chmod0444, and SHA-256 recorded. Only that input directory is mounted read-only, replacing the shared workspace mount. The input hashes are rechecked before accepting a terminal outcome. The existing independent three-second container deadline and isolation controls remain.

A terminal record binds exact container ID/image, stopped-state observation, exit code, outcome, input hashes and optional result hash. `inspect_diagnostic_record.py` verifies the saved record offline without running Docker or a worker. It distinguishes completed, timed_out and cancelled evidence; missing/changed/unsupported evidence yields unknown, never success or retry authority. Live worker state is explicitly not observed. These are trusted local operator records, not signed independent attestation against a malicious operator who can rewrite the entire package.

## Tests and recovery

Actual revision3 diagnosis/deadline/cancel runs all completed with verified stopped workers and cleanup. For each of the three records:

- Original recorded outcome verified.
- A cold file-tree copy produced the same inspection result.
- Removing terminal evidence yielded unknown.
- Altering the copied evidence fixture yielded unknown.

All three job directories were copied to HAL under `C:\Users\wasch\Documents\Codex\2026-09-29\continue-step-one-of-the-windance\bounded-job-recovery-20261002`. The same read-only inspector independently verified their input/result hashes and terminal bindings on HAL as completed, cancelled and timed_out respectively. No job was re-executed during restoration. Sanitized result summaries accompany this packet.

Use the inspector on a preserved job directory for offline verification; it cannot release holds, start jobs or determine present Docker state. Missing receipt after coordinator interruption remains unknown pending exact live-container observation. Never rerun work simply because a record is missing. No rollback needed; production services were not changed.

## Remaining limits

General authenticated submit/status/log/cancel/result interface, persistent deduplication, automatic coordinator reconciliation, host-reboot/power-loss behavior, global wall-clock control, arbitrary/untrusted worker isolation, contradictory-evidence handling and reasoning acceptance are unfinished. Output size is checked after capture rather than enforced during streaming. Job input copies are version-bound against accidental drift, not protected from a privileged host actor. Atomic status replacement does not prove directory durability across power loss. The prototype does not satisfy the entire Phase4 gate.

No actual mailbox/send/Odoo/dispatch/model call or SAM interruption occurred. Warden stays suspended, phone/Level8 disabled and SyncThing unchanged. Application model usage zero; total project cost unmeasured. Latest full email stage remains separate at `/Users/herald/backups/email-action-route-20261002`; no email deployment was performed by this work.
