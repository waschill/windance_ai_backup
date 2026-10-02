# Email candidate private-data and full application recovery

October 2 UTC / October 1 Mountain 2026. Candidate remains staged; live source unchanged.

A fresh SQLite online backup used read-only access to the live Harness database. Two isolated copies ran the unchanged source and the staged email-intent candidate respectively. Environment-owned data/config/log/Google paths were redirected before import. The full module imported and actual FastAPI ASGI lifespan startup/shutdown and GET /health ran; health returned200 for both. Runtime audit hooks denied outbound socket connections/process launches, mailbox/model/staff adapters rejected calls, and startup audit was intercepted/count-checked. This tests the full application lifecycle without exercising actual Google credentials or production networking.

Initial comparison stopped because sqlite_sequence changed. Read-only investigation identified that internal table only; no private rows were displayed. A fresh baseline-versus-candidate run established the same sequence movement in unchanged startup. This is consistent with existing seed INSERT ON CONFLICT handling, not a candidate regression. All28 non-sequence tables remained identical to the snapshot; all original tables, including the sequence table, matched baseline startup exactly. Candidate added only an empty email_action_intents table.

Each initialized WAL database was captured with SQLite backup, not a raw live file copy. The cold-restored candidate matched all candidate tables and passed integrity. Seven stable source/module/database files were copied to HAL and hash-verified; all four database copies independently passed integrity and table comparisons there. No full application source, private mail, report identifiers, credentials or database rows were published.

## Recovery locations and reproduction

Accepted HERALD directory: `/Users/herald/backups/email-private-recovery-20261002T031556Z`.
HAL stable-file copy: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-private-recovery`.
manifest.private.json hashes original/candidate source, journal, original snapshot, baseline-initialized DB, candidate-initialized DB and cold DB. The earlier031444Z directory retains the failed first comparison; use031556Z for accepted evidence. Scratch app/config folders remain private on HERALD and are not part of the stable-file manifest.

Verify manifest hashes, then restore the snapshot to a new private scratch path, set all app/Google config paths to that scratch directory, retain the external-call denial and mailbox/model/dispatch guards, run the exact pinned ASGI lifecycle, and compare against a separately initialized baseline copy. The archived test is the executable specification. Do not run an uncontrolled restored server or a mailbox report as a recovery test. The snapshot is evidence, not permission to rewind live accepted work.

Exact candidate source4fb5bc825bc95e5fbfa5e6c68ac2fb0afab9b6ba9a6bcb0e71fb357c7772e19c and journal27bffb8be2b13de26ca6fb816c538d6f435b70e7f1831ab6c641f792a027e451 remain private/staged. Live source0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0 was verified before this test. No production services, schema, schedules or data were changed.

Limits: audit side effects intercepted; no actual TCP listener, authentication/credential recovery, background workers, real Gmail classifier/action, old-snapshot intent reconciliation or host replacement was proven. The new table is empty in current live data, so preservation of existing unknown intents is covered by separate synthetic process tests, not this snapshot. Cross-path action admission and authoritative per-operation recovery remain deployment gates. Application model calls zero; Codex cost unknown. Phase1 open; SAM/Odoo design and Node-RED access remain separate unresolved work. Warden/detailed notes stay suspended, phone/Level8 disabled, SyncThing unchanged.
