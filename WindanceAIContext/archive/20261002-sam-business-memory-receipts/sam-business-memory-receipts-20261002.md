# Atomic SAM business-source receipts — October 2, 2026 UTC

Staged isolated storage component; not a route, migration, service or SAM deployment. No personal-memory records, mirrors, vectors, Odoo calls or business readers are exposed.

`sam_business_memory.py` composes the dedicated producer admission contract with two explicitly installed SQLite tables: current SAM business source per date, and stable event receipts. Producer identity is fixed by admission; it is not a claim that SAM is William or Shawn. The caller must supply a stable event ID and expected revision separately from the established legacy payload. Source/content/revision and event receipt commit atomically under an immediate transaction.

Identical event replay returns the original receipt, explicitly marking it superseded if a newer revision exists. Changed payload or expected revision under the same event conflicts. A new event can update only the exact current revision. Current content hash mismatch or receipt/source inconsistency holds rather than overwriting or falsely acknowledging. Returned receipts contain metadata/content hash, not summary text.

## Isolated verification

- Eight concurrent identical requests: one new source/receipt commit, seven replays, all revision1.
- Changed request under same event: rejected.
- Explicit correction with expected revision1: revision2.
- Replay of original event: original revision1 receipt marked superseded; revision2 retained.
- Stale revision and wrong credential: rejected.
- Injected receipt-insert failure: source correction rolled back, leaving exactly two accepted receipts.
- Consistent cold SQLite backup: identical replay response.
- Altered stored summary: rejected because its content hash no longer matches.

All data/credentials were synthetic and temporary, no external calls or production changes. This is transaction behavior, not proof of natural commits or complete memory privacy. Summary text remains a producer statement, not independently verified business truth.

## Integration requirements

The actual SAM client currently lacks this event/revision envelope. It must persist an event identity before sending, retry the same payload/identity after uncertainty, verify matching receipt date/content/revision and handle `superseded` honestly before marking its local day committed. A plain statusok is insufficient for this new protocol. Do not silently adapt a superseded receipt into current-write success or infer a new event from retry time.

No route is installed and no legacy write/read path is retired. Canonical business-reader authorization, source-retention/correction semantics, live credential transport, schema backup/recovery, old-backup reconciliation and actual client/server failure composition remain gates. The separate tables are a staged source-store candidate, not authority to migrate legacy/private memory or invent human ownership. At-rest encryption and host-compromise resistance are not tested. Restoring a snapshot predating later corrections needs source reconciliation; the tested consistent backup does not solve that case.

SAM protected hours, suspended detailed notes, Warden suspension, Odoo restrictions, SyncThing and disabled phone/Level8 remain unchanged. No application model call or new paid commitment. Project dollars remain unknown. No production rollback needed; Phase1 and project remain open.
