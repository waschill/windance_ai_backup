# Staff watchlist recovery — 2026-09-17

Status: TRACKING AND SEARCH REPAIRS APPLIED AND VERIFIED; CLEAN WATCHLIST FOLLOW-UP STAGED, NOT EXECUTED.

William asked for entertaining agentic AI videos pertinent to the existing assistant setup, excluding Goldie. The original staff report failed to provide links.

## Verified causes and applied repairs

- The shared model bridge treated the words Kanban and create as an explicit task-creation request, even when they appeared in a prohibition. It injected the opposite instruction and falsely characterized subsequent tool results as completed tracking operations. That inference and injection machinery have been removed. Genuine task-creation requests retain their original instructions and tool inventory.
- The search error identified the local search service, not YouTube. The production service context failed its Python connection while native transport could reach the same service. A bounded retry now uses that same service without changing search providers. The real production staff run recovered four searches this way.
- Entertainment watchlists now have a scoped citation/format contract, distinct video-link counting, and continued independent QA. High-stakes and software-version gates remain.
- Thirty regression tests passed. Bridge and task service health checks passed after deployment. The live canary had no Kanban calls and no outbound delivery receipts.

## Remaining work — do not claim completion

The first real canary finished PARTIAL. Its initial placeholder links were rejected by the deterministic gate. Its correction retrieved links but guessed some metadata; QA then confused trailing audit instructions with draft content.

A follow-up is staged to supply verified YouTube titles/creators and to separate the draft clearly from QA instructions. This follow-up has NOT been tested or deployed. Mandatory Claude review was interrupted by a provider credit error; a fresh session then reported unavailable credentials. William was asked whether to restore reviewer access or explicitly exempt this narrow follow-up. No exception is recorded yet. Do not execute the staged follow-up without completed review or William's explicit exception.

## Review, use and recovery

The applied revision received completed Claude review in session 20260917_145404_848a0d. Revision manifest SHA-256: 26a8245374bcc08f9490872e4f435ee0b306eee3200a75a08bb467cf7e42fa09. All findings affecting safe execution were resolved or dispositioned before execution. The actual API response wrapper, production launcher and internal delivery suppression were verified.

Fresh staff assignments load the repaired runner and search provider. Existing gateway processes can retain older imports until their normal restart. No old tasks were replayed and no pending queue was swept. No model/provider upgrade or unrelated system change occurred.

Detailed source, tests, review and rollback evidence remain in the local operator packets named staff-repair-20260917 and staff-watchlist-20260917. The former contains the applied revision and exact backups; the latter contains unexecuted follow-up work. Use only the applied revision's reviewed rollback procedure, with its drift checks and idle-runner requirement. Preserve/retest the search-provider patch during a future Hermes upgrade.

## Publication boundary

Live repository metadata reported the established backup repository PUBLIC, contrary to earlier descriptions of it as private. Only this sanitized operating note is added to shared context; detailed source/review packets are retained locally. No repository visibility or permissions were changed.
