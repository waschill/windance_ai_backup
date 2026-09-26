# Syncthing Business ownership repair — 2026-09-26

William explicitly requested diagnosis and repair of Business stuck at 67 pending items. Live AL Syncthing was connected to HAL but had 15 pull errors creating directories, with retry backoff reaching 1h4m. The 67 pending items were 64 files and three directories (268,852,593 bytes).

## Cause and applied repair

The earlier Odyssey NFS repair maps AL to rsync_backup UID 1003/GID 998. Existing Business entries owned by UID 1000 retained modes 0755/0644. Their POSIX ACL mask removed effective write access for named UID 1003 despite its rwx ACL entry. Reading/scanning therefore worked while creating directories and versioning files failed.

Vega saved a private per-path ownership/mode manifest at Odyssey /Volume2/docker/vega-backups/syncthing-business-owner-20260926/ownership-before.json. Changed only owner UID 1000 to the configured backup UID 1003 on 612 existing non-symlink entries within /Volume2/syncthing/data/business (92 directories, 520 files, including relevant version history). Verified all resulting UIDs and unchanged groups/modes. No recursive permission broadening, export change, database reset, or source-file rewrite was used.

A create/remove-directory canary as the actual container runtime account succeeded in the previously blocked archive directory. Requested Business scan, then briefly paused/resumed only Business to clear its retry backoff. Its original unpaused state was restored. Existing schedules and other folder configuration remain unchanged.

## Verification and operation

At approximately 00:25 MDT, AL REST db/status reported idle, needTotalItems=0, needBytes=0, errors=0, pullErrors=0, and localFiles=globalFiles=46575. Folder error list was empty. Container logs independently confirmed document transfers and the 268,423,168-byte Second Brain database transfer. New folders/files are created as UID 1003 through the existing NFS mapping, so inherited source permission modes no longer lock out their owner.

The SAL dashboard polls Business every 300 seconds; the underlying live API is authoritative between polls. Warden was already paused before this task; pause was confirmed and its pre-existing paused state was preserved to avoid overriding separate maintenance.

## Recovery and limits

The private ownership manifest records each prior owner/group/mode. If the NFS identity is deliberately changed later, review ownership together with that mapping. Do not blindly restore UID 1000 while the export still maps to UID 1003. File content/version data was preserved. Only Business ownership was repaired; this does not certify every folder's ownership or future source availability. Canonical publication adds normal new synchronization work after the zero-pending verification.
