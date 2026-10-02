# Actual SAM renderer and staged producer admission — October 2, 2026 UTC

Fresh read-only source inspection and isolated HAL test. SAM was not restarted, interrupted or used to execute tests during its protected interval. No production API, database or Odoo call was made.

The source copied privately from the active SAM path matches SHA-256 `824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1`. Only its actual `commit_day` function was compiled into the disposable fixture. Schedule retrieval, rollover, Odoo history posting, HTTP, logging and database dependencies were supplied as synthetic adapters/temporary SQLite. No actual training notes or horse data were used; detailed-note collection remains suspended.

## Observed compatibility

| Case | Rendered UTF-8 bytes | Initial local commit | Admission attempts |
|---|---:|---|---:|
| Empty day | 240 | yes | 1 |
| Mixed Training/Farrier/Vet | 288 | yes | 1 |
| Unicode fixture | 294 | yes | 1 |
| Deliberately oversized | 65807 | no | 0 |
| Lost first acknowledgment | 288 | no | 2 after explicit same-day retry |

Already-committed synthetic days did not repost. The lost-response retry produced an identical content hash. This proves actual renderer shape compatibility for these fixtures and the need for receiver idempotency; it does not prove duplicate writes are prevented, because the admission component performs no storage. The live service still uses the broad legacy endpoint and existing acknowledgment behavior. Previously staged stronger SAM acknowledgment/history/clear work is separate and remains undeployed.

The first fixture run encountered a Windows temporary-database cleanup failure because its test connector did not close SQLite connections. The fixture now uses a closing connection subclass; accepted run passed, and the earlier synthetic temporary file/directory were explicitly removed. No SAM connection implementation was changed by that test correction.

## Remaining acceptance

Implement receiver receipts binding producer/event/date/content/revision and preserve retries after uncertain acknowledgment without overwriting a newer record. Verify actual credential transport, content validation and canonical business-source reader policy before replacing the legacy route. Maximum real summary sizes are unmeasured: the64KiB bound is only tested with synthetic content. Real HTTP compatibility, storage atomicity, cross-day/revision behavior and natural commits are not proven here.

Private source copy stays in the local workspace and is excluded from this published packet. The sanitized test pins its hash and contains no actual source data, secrets or notes. No service/route/model changes, sends, staff dispatch or paid installation occurred. Warden/SyncThing/Level8/phone boundaries preserved; Phase1 and project remain open. No production rollback needed.
