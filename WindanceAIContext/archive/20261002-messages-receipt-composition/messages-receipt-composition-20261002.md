# Exact attributed receipt composition — October 2

Staged messages_attributed_receipt.py combines the pinned attributed-text decoder with the preceding read-only direct-iMessage observer. The original plain-text helper remains unchanged. No live sender, caller, queue, scheduler or receipt schema was changed.

## Verified behavior

Twenty-five actual SQLite/decoder composition scenarios pass on HAL and SAL using synthetic Foundation archives: plain and attributed exact matches, Unicode, agreement/conflict between text representations, sent-only, wrong recipient, group, stale boundary, duplicate, incoming, SMS, recorded/null errors, absent delivery date, malformed archive, wrong root, substring-only text/metadata, unknown candidate plus exact match, oversized archive, candidate overflow, multiple chat joins, missing content, unrelated decodable candidate plus exact match. Five invalid boundary inputs reject; a missing database is not created. Each synthetic database hash stays unchanged and outputs omit body/recipient.

The observer selects only outgoing iMessage rows after the supplied row boundary, with exactly one chat association and exactly one member whose handle matches the expected recipient. It scans at most100 eligible candidates plus an overflow sentinel, bounds field sizes before materialization, uses readonlySQLite/query_only and the existing lock/query-operation limits. Exact match alone is insufficient: one match, error0, sent1, delivered1 and positive delivery date are all required. Successful output reports local Messages flags, not human reading.

Unreadable or conflicting candidate content prevents a delivered result even when another exact match exists, because the unknown row could hide a duplicate. Overflow remains unconfirmed; no truncation-to-success or substring fallback. Multiple exact matches report ambiguous. This conservative behavior can hold an otherwise valid message when an unrelated unreadable candidate shares the window; narrow trusted request windows and full correlation are still required.

## Incomplete integration gates

The observer accepts a supplied boundary; it does not establish that boundary's provenance. It does not persist request/chunk identity, prevent two requests claiming the same row, or orchestrate multiple chunks. It does not provide the full-process deadline/RSS supervisor; decoder invocation must be placed in that bounded worker before any live integration. Its Python/SQLite limits alone do not bound all parser work. No real matched message or delivery was claimed in this turn, and no natural training pilot pass was added.

Next: combine durable trusted pre-send boundary/chunk correlation, exclusive receipt-row claims, crash recovery and supervised observation with the actual outbox contract. A successful osascript exit must remain submitted until independent delivery evidence is present. Unknown outcomes must not automatically resend. Coordinate consumer/schema migration and verify backups before installation.

## Reproduction and recovery

Run test_messages_attributed_receipt.py with the pinned pytypedstream0.1.0 wheel path and attributed-fixtures-20261002.json from the preceding decoder packet. Wheel hash499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278 is verified before direct import; no pip installation. Candidate/tests are in the HAL workspace and SAL/tmp, not active sender directories. No production rollback is needed; do not replace the live sender with these modules alone.

No real Messages body read in this turn; no send, model call, paid commitment, SAM/Odoo mutation, Warden/phone activation, SyncThing/Level8 or route change. Codex cost unknown. Phase1 remains open. Node-RED browser restriction remains separate; no alternate access attempted.
