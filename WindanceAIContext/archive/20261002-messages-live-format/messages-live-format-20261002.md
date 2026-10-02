# Messages live-format coverage — October 2

## Verified observation

SAL read-only sample of the latest100 outgoing iMessage rows:100 attributed archives,99 decoded,1 rejected,0 oversize,0 plain-text fields. No bodies, recipients or message identifiers were exported or written. The output is aggregate counts only. Worker elapsed0.0634seconds; sampled peakRSS18,208KiB. This is parser coverage, not exact-content correctness against an independent oracle and not evidence of a particular delivery. No pilot acceptance increment.

The candidate and pinned wheel are the exact staged decoder evaluated in archive/20261002-messages-attributed-decoder. The one rejected record remains unsupported/unconfirmed; its content was not extracted for diagnosis. Never replace rejection with a substring fallback. No sender or receipt consumer has been modified.

## Isolation and limitations

The child uses readonlySQLite URI, query_only,2-secondSQLite lock wait,100,000-operation query budget,100-row limit,256KiB archive and20,000-character plain-text materialization limits. CPU limit5seconds, worker alarm10seconds and parent wall deadline15seconds bound execution. Core dumps disabled. Python audit hook rejects network/subprocess/system execution and Python-level writes and unexpected SQLite paths after decoder import. This trusted-worker audit is not an OS capability sandbox.

macOS rejected RLIMIT_DATA before reading any messages. The final runner instead samples childRSS via ps every~50ms and kills it above256MiB; transient peaks between observations are possible, so this is explicitly not a hard allocation ceiling. A ps lookup has a1-second timeout and missing observations fail closed unless child is terminal. Child stdout/stderr captured; only fixed-schema counts or sanitized failures are exposed. Input caps further limit materialized rows; parser hardening for arbitrary adversarial archives remains unproven.

The first database attempt also stopped before opening because this SAL Python emits sqlite3.connect audit paths as bytes; a synthetic nonexistent readonlyURI probe established that behavior. Guard now accepts only the same exact fixed URI as UTF8bytes or string. No broader path access was added. One inline shell diagnostic failed quoting; file-based synthetic diagnostic replaced it. None of these attempts sent messages or changed production state.

## Next step and recovery

Integrate the exact decoder into the staged observer with bounded full-worker execution, recipient/direct-chat restrictions and ambiguity checks. Persist trusted pre-send row boundary and per-chunk request correlation before sender integration; require actual sent/delivered/error flags. Unrecognized archives or resource failures must remain unconfirmed, and must not cause automatic replay. Do not equate local delivered flags with human reading.

Included script and aggregate JSON reproduce the observation structure; current message counts may change naturally. Script resides in the HAL workspace and SAL/tmp; wheel remains a test artifact imported without pip install. No production rollback is necessary. No SAM/Odoo/SyncThing/Level8/Warden/phone or model-route change, send, scheduling or dispatch occurred. No new paid commitment/application inference; Codex cost unknown. Phase1 remains open. Browser-policy-blocked Node-RED alarm repair remains separately unresolved and was not accessed through this work.
