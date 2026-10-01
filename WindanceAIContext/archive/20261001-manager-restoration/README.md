# Selected manager HTTP application restoration — October1, 2026 UTC

Result: PASS for this bounded rehearsal. Two HTTP application starts returned the three restored projects, preserving status, owner, report hash and delivery fields. All3project,24stage and98event rows were unchanged. Background workers, sending, scheduling and dispatch remained disabled. This is stronger than cold parsing but is not full manager/host recovery.

## Inputs

- Exact manager source SHA256:1d2c67417ca4080158db8e5c9840b5c602523856bfc7551ad0f2c8276a4c7a83.
- Selected database SHA256:66c0d5043d10d09882411e7b8a095a974fef5f7378c485a411ad5602739ef0f0.
- Fresh source: HERALD /Users/herald/backups/agentic-baseline-20261001T0025Z;61artifacts cold-verified and independently copied/hash-verified on HAL.
- Private AL rehearsal inputs: /home/waschilladmin/backups/manager-isolation-20261001T0035Z. This contains the selected database and must stay private. No raw database is published.
- Existing AL image sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f supplied Python3.11.16 and aiohttp3.13.5. No image download or software install. This differs from production Python3.11.15 and does not establish native macOS dependency parity.

## Boundary and execution

Created only disposable container windance-manager-restore-20261001t0035. Before execution, inspected its settings: network none, no published ports, root filesystem read-only, one read-only input bind, user1000:1000, all capabilities dropped, no-new-privileges,256MiB memory,0.5CPU,32PID limit, no restart policy,64MiB temporary filesystem. No host Docker socket, private configuration, credentials, live database, service directory or production volume was mounted.

The test independently asserted that only interface lo existed and the production bridge-token path was absent. It verified both input hashes, copied the selected DB into temporary storage, imported the unchanged manager source, then suppressed its cleanup lifecycle and replaced worker/send/upstream entrypoints with rejecting test guards. It initialized only the temporary schema and served the actual unmodified HTTP handlers on an ephemeral loopback port inside the isolated namespace.

GET health returned200 with status starting and no tick, exactly as expected for intentionally suppressed workers. It was NOT called operationally healthy. GET project list/details returned all expected records and stage counts; source rows and input hashes remained identical. No HTTP writes were exercised. The HTTP application was stopped and started again against the same temporary database with the same results. This was an application restart within one container process, not a host reboot or crash-injection test.

The container exited0 at2026-10-01T00:35:26.866Z, with no OOM and zero blocked-operation attempts. Measured test body0.081seconds excludes setup, copying, image provisioning, credential recovery and worker recovery; it is NOT an RTO. The image's inherited healthcheck had no logged executions before exit; its stopped-container unhealthy label is not this test verdict. For a repeat, explicitly add --no-healthcheck as well as overriding the image entrypoint to Python.

After recording exit/config receipts, removed only this disposable container and its anonymous volumes. Private input backups remain. AL's preexisting containers still showed their existing uptime, and both Open WebUI instances remained healthy. No live service or Warden state was changed.

## Repeat procedure

Use a fresh private directory and container name, never a live service volume. Verify input hashes against the private backup manifest, use the archived restore_manager_isolated.py, and preserve all boundary flags above with --no-healthcheck. Execute Python with /audit/restore_manager_isolated.py as its sole script, with the private directory mounted read-only at /audit. Inspect configuration before starting. Require exit0, expected starting health, unchanged rows/hashes and zero operation attempts. Retain sanitized results, then remove only the named test container. Never start the ordinary manager entrypoint against restored production queues.

## Remaining recovery work

Full messages/state, private configuration, schema indexes/triggers omitted from selected exports, actual worker/model authentication, cancellation and uncertain-operation reconciliation are not covered. Warden-held production Harness registration remains untouched. No production service was repaired by this rehearsal. This result satisfies a selected isolated HTTP/state-restoration subtest only; continue targeted recovery and business acceptance before advancing the project gate.
