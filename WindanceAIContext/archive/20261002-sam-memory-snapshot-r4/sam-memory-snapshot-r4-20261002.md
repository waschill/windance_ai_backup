# SAM staged commit snapshot revision 4

The failed r3 integration is preserved. New private r4 main SHA-256 is db71ccb2da8f794ba21f0fb1cf74995890acf8bbb94c436b680dc76e630ee816. The new sam_commit_snapshot helper is a2c688452ecd181bef56c7be5d6e6a36b87ae9ef69c49cf0d7c1341a706c51ff. Full private source and six-file manifest remain in the HAL project workspace under sam-memory-r4-private, outside shared publication.

The candidate records a date-bound input hash before effects and freezes the rendered memory payload plus result metadata before transmission. Retry requires the same schedule items and existing rendered training-detail inputs, then reuses the frozen payload and original trigger instead of rerunning history/rollover. This reads existing details only; it does not enable collection. Missing endpoint/credential-file configuration now refuses before effects. This is a presence check, not verified credential validity or endpoint reachability.

## Verified evidence

test_sam_memory_r4.py verifies the six-file manifest and extracts the actual candidate connect, init_db, history posting, memory helper and commit functions. Real temporary SQLite client/receiver stores are used; Odoo, transport and rollover are synthetic. Eleven scenarios pass:

- Normal commit and repeated already-committed calls.
- Receiver commits but first response is lost: two attempts, one event/receiver commit, one history create and clear, successful local completion.
- Wrong event receipt: one receiver commit, local remains uncommitted through three attempts.
- Missing configuration: zero history, clear or memory effects.
- Unknown history or clear outcomes and false clear acknowledgment: no duplicate effects and no local completion.
- Failed local clear receipt insertion: retries reuse confirmed intent and preserve a newer synthetic need.
- Changed schedule after lost response: snapshot conflict holds without another memory request.
- Closed-database cold copy plus reloaded function definitions: identical pending event recovers without duplicate writes. This is not an OS/process restart or whole-service restore.
- Automatic/manual trigger changes across retry preserve the original prepared summary and receipt identity.

All tested databases pass integrity_check and are closed/removed. No real remote call, model call, send, dispatch, production service change or SAM interruption occurred. Codex account usage is separate; project-attributable dollar cost is unknown.

## Remaining gates

This fixes the demonstrated post-transmission retry deadlock only. Actual rollover and crashes before snapshot freeze still require composition tests: already-posted history and earlier carry effects may be omitted from a subsequently generated summary. Existing snapshot rows intentionally hold later changed input; a supported correction/recommit path is not implemented. Concurrent schedule mutation between initial read and local committed update is not protected by an atomic revision comparison. First-clear Odoo Boolean request-generation safety remains unresolved. Credential validity, TLS, full startup, actual transport composition and private whole-package restoration remain unverified. Candidate is not deployment-ready; Phase 1 remains open.

## Recovery

Nothing was installed; no production rollback is needed. Preserve both private revisions and their manifests. The shared build script composes r4 only from the exact pinned r3 and refuses an existing destination. The shared test requires the private stage and existing receiver modules in the original workspace; this packet is not a standalone recovery bundle. Do not replace live SAM with this candidate based on these tests.
