# Consolidated diagnostic source recovery package — October 2, 2026 UTC

Created one exact versioned package for the staged diagnostic implementation. This is a source/component recovery package, not a deployed service or complete host/application backup. Phase1 and the project remain open.

## Contents and verification

`diagnostic-recovery-package-20261002.zip` SHA-256:
`f802dd776627b4cce235ea82b14773c05e6564d0af65a9f41fddc92b5296afc1`.

Ten manifest-pinned files: three HERALD API/ledger/remote-adapter modules, six AL worker/launcher/remote/cancel/inspector/fixture files, and one no-dispatch API validation script. Nine runtime/fixture hashes were freshly read from the actual staged host files and independently matched HAL sources before packaging. The archive includes host placement, exact observed Python dependency versions, pinned image identity and exclusions. No credentials, operational databases, private messages, service definitions or image bytes are included.

HAL independently verified archive/member hashes, safe relative paths, bounded member size, isolated extraction and Python compilation. HERALD repeated this verification and executed the restored API validation from the extracted package: twelve checks passed with dispatch_calls0 and no worker execution. Tests use temporary SQLite and synthetic credentials. The verifier removes its disposable extraction directory. It does not install packages, start listeners, enable schedules or run worker scripts.

Observed HERALD runtime: Python3.11.15, FastAPI0.133.1, Starlette1.3.1, Pydantic2.13.4, Uvicorn0.41.0, HTTPX0.28.1. These are observed versions, not a fully captured dependency environment. AL image requirement remains the existing pinned Open WebUI image; its startup is overridden for the diagnostic and production volumes are never mounted.

## Restore instructions

1. Verify the archive SHA against this record before extraction. Use `verify_diagnostic_recovery_package.py ARCHIVE EXPECTED_SHA` for isolated verification only.
2. On HERALD's existing compatible Python environment, append `--test-api` for the no-dispatch restored API checks. Do not run AL worker scripts just to validate backup contents.
3. Preserve existing records/configuration before any later deployment. Configure real identity and persistent storage only through the remaining deployment gates; this package deliberately has neither credentials nor a service installer.
4. Remote adapter paths still point to `/tmp/windance-bounded-diagnosis-20261002`. That is a test dependency, not a production destination. Changing it requires a new pinned package and integration verification. Do not assume unpacking arbitrary directories makes the worker deployable.
5. Restore job databases using consistent SQLite backups and preserve request IDs, claims and uncertain states. This source archive does not contain those live data. Earlier test job/cold-ledger recovery evidence remains separate.

## Fresh operational observations

AL Docker inspection found zero remaining `windance-diagnosis-*` containers. Production `open-webui` reported healthy/up6days; an older stopped Open WebUI container was preserved. HERALD Harness8791, bridge8793 and manager8797 each returned HTTP200. These are point-in-time availability checks, not complete network/workflow or delivery acceptance. No service was restarted, no stopped historical container removed, and no production state changed.

## Open gates

Real-user credentials, persistent deployment/storage, UI integration, complete diagnostic evidence/reasoning acceptance, input/output streaming bounds, remaining race/crash/power-loss scenarios and independent outcome semantics remain incomplete. This verified component restore does not establish bare-machine recovery or project completion. Warden restoration remains reserved for actual project completion. SAM protected hours, disabled phone/Level8 and SyncThing rules remain unchanged.

No application model calls, business sends or operational staff dispatch occurred. No new software or paid commitment. Latest account checkpoint remains78% weekly used/22% remaining, not requeried here. Project dollar cost remains unknown. Canonical archive retains the package, builder, verifier and this record for future work.
