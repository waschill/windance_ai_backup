# Checkpoint-bound staged receipts — October 2

The staged coordinator now captures the actual readonly Messages checkpoint, saves it in the same transaction as attempting state, and passes that saved checkpoint through the bounded observer stdin. The observer begins a SQLite read transaction and verifies store/anchor both before and after the exact candidate query on that same connection/view. Any mismatch remains unconfirmed and persists the request hold. A missing saved checkpoint cannot proceed through the coordinator. No separate capture-after-send is used as a substitute for a query-bound check.

Journal schema now3 for checkpoint_json; only fresh disposable test databases provisioned. Previous staged versions reject; no migration or production files changed. Standalone low-level journal/observer methods retain optional checkpoint arguments for prior tests/internal use, but the staged coordinator requires capture and refuses an absent checkpoint. These are trusted internal methods, not an exposed authorization interface. Production wrapping must not expose unbound alternatives.

## Verified

Seven actual send_one/real decoder/real supervised observer/journal composition scenarios pass on SAL, each followed by two restarts: normal two-chunk delivery, sent-only hold, exit after attempt, exit after send, exit after receipt, replacing Messages file after send, and changing the saved anchor GUID after send. Replacement/anchor-change cases each retain exactly one synthetic sent row and hold remaining work across restarts. The fixture includes a preexisting GUID-bearing seed row; captures now use real checkpoint logic rather than a constant synthetic store identifier.

HAL checkpoint regressions, journal/concurrency/cold-copy/missing-history regressions,25 exact-observer cases and four journal abrupt-exit cases also pass against this revision. All database bodies are synthetic. No actual osascript/Message send or live Messages body access; the unchanged production send_one has its subprocess call intercepted. This remains selected-function composition; actual daemon handle/main queue transitions are not installed/wired.

## Limits and next gate

Same-inode rollback retaining the compared root/anchor/high-water is not universally detectable. File-stat checks are not an OS snapshot/anti-tamper mechanism. Prior CPU/wall/RSS and trusted-worker limitations remain. Capture is currently a direct readonly helper with SQLite limits; it needs the complete request supervisor before production use. Query checkpoints bind an observation at its time, not future immutable receipt history. Local delivered flags do not mean human reading.

Next complete queue-handler/owner-lock integration and delayed-receipt behavior, fit whole-request deadlines to consumers, package/pin all modules, verify coherent backups and establish a forward-only activation boundary excluding legacy uncertain work. No natural pilot pass. Do not install only these partial modules. No real sender, scheduler, task dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route or paid commitment change. Codex cost unknown; Phase1 remains open.

## Recovery/reproduction

Included matching candidate modules and composition test are the schema3 revision. Test with pinned wheel499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278, pinned daemonf90fc54f and original synthetic Foundation fixture JSON. Workspace and SAL/tmp only; no production rollback needed. Older prototype databases must not be silently reinitialized or promoted; a future migration requires an explicit reviewed recovery path preserving attempt history.
