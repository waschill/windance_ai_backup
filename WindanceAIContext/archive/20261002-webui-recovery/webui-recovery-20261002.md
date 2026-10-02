# WebUI application-data recovery evidence

Verified October 2 UTC / October 1 Mountain, 2026. Phase 1 remains open.

Production `open-webui` and lab `truth-engine-lab` application data now have private AL backups and independently verified HAL copies. Each contains two SQLite databases and three stable files. All file hashes, SQLite integrity checks and every non-internal table's semantic hash match the private manifests on HAL. Production's one uploaded-file reference resolves to its captured upload. This closes the baseline's missing application-data copy evidence, not the full-volume or bare-host recovery gap.

## Evidence and limits

- Production snapshot contains one user, 22 chats, one file and two filter functions; lab contains zero users/chats/files/functions. No private record contents or upload names are published.
- Existing image is Open WebUI 0.11.4, `sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f`.
- Separate cold data clones were mounted into this cached image with no network, no exposed ports, read-only container root, temporary `/tmp`, one CPU, 2 GB memory and 128-process limit. Only Python application model imports and user/file count queries ran; no web server, model inference, sending, scheduling or task dispatch was enabled. Actual async ORM queries returned production user/file counts 1/1 and lab 0/0.
- First application read failed because authentication requires a signing key. The retry used a random temporary signing key generated inside the test process, never exported or persisted. Production credentials were not used. Existing login/session recovery is explicitly untested.
- Online SQLite backups were individually consistent and matched source table hashes immediately after capture. The two databases and upload are not a single transactional multi-file snapshot. Cache was excluded, including cached models; offline inference after full-host loss remains unproven.
- Container environment secrets, deployment credentials and complete host configuration were not exported. No full image archive was created; future recovery requires the verified image to remain available or be obtained from its trusted source. Custom filter bodies are present only in the private database; no filter execution or source review was part of this test.
- Final `docker ps` inspection showed both original WebUI containers healthy with five-day uptime and no cold test containers remaining. Production was not restarted or reconfigured.
- HAL copy command initially failed at PowerShell parsing before execution. Corrected command completed, then an independent Python immutable-database verifier passed. Failed first ORM receipt is retained alongside the passing retry.
- No application model calls or paid resources were added. Codex execution cost and total operating cost remain unknown; these tests do not establish a monthly estimate.

## Private recovery locations

AL: `/home/waschilladmin/backups/webui-recovery-20261002/{open-webui,truth-engine-lab}`.

HAL: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-webui\{open-webui,truth-engine-lab}`.

Each HAL directory contains original `data`, `private-manifest.json` and non-secret `deployment-metadata.json`. AL also retains disposable `cold-data` and private test logs. Treat all application files and manifests as private; never commit them or publish their contents. HAL is off-host from AL, not proven off-site disaster recovery.

## Recovery procedure

1. Reconcile current owner activity and choose the specific instance. Confirm the intended recovery point; restoring this snapshot loses subsequent changes unless they are reconciled separately. Preserve a fresh backup of current data first. Do not overwrite the running volume.
2. Verify every `data` file against `private-manifest.json`. Run `verify_webui_offhost.py` on HAL for immutable SQLite integrity and all-table comparisons. Adapt paths explicitly for a different recovery location; do not weaken comparisons.
3. Copy the verified original `data` to a new isolated directory. Never reuse the modified cold test clone as the original recovery source. Check the recorded image ID exists locally. Use the Docker isolation arguments and Python-only entry point in `retry_webui_cold_models.py`; provide a newly generated ephemeral test key and keep network and published ports disabled. That script's existing paths are an audit fixture; choose a fresh recovery root before reuse.
4. Require successful application-model reads and expected manifest counts. Inspect failures privately. Passing this step establishes only data readability. Before any live cutover, separately reconcile persisted configuration, credentials/signing key, cached-model dependencies, uploads, custom filters and authentication behavior.
5. Plan an explicit instance-specific maintenance window and rollback with fresh current-data backup. Configure the intended account/login policy before exposing a restored server; the empty lab's first-admin bootstrap remains an unresolved boundary. Verify intended-user access and cross-user denial before accepting the interface. No production cutover was performed or authorized by this recovery record alone.

## Next project gates

Authenticated interface and knowledge workflows, empty-lab ownership/containment, source-backed memory integration, bounded diagnostic jobs and natural report delivery acceptance remain open. Shawn's actual-training-note pilot remains owner-deferred. Warden stays suspended until project completion; phone and Level 8 stay disabled, SyncThing unchanged. Node-RED alarm restoration is separately approved but browser-policy blocked.
