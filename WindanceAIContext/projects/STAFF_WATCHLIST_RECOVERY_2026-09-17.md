# Staff watchlist recovery — 2026-09-17

Status: APPLIED AND VERIFIED, including a completed production Scout/Athena watchlist.

William asked for entertaining agentic AI videos pertinent to the existing assistant setup, excluding Goldie. The original staff report failed to provide links.

## Verified causes and repairs

- The shared model bridge treated the words Kanban and create as an explicit task-creation request, even inside a prohibition. It injected the opposite instruction and falsely characterized subsequent tool results as completed tracking operations. That inference and injection machinery have been removed. Genuine task-creation requests retain their original instructions and tool inventory.
- The search error identified the local search service, not YouTube. The production service context failed its Python connection while native transport could reach the same service. A bounded retry now uses that same service without changing search providers. The real production staff run recovered four searches this way.
- Entertainment watchlists have a scoped citation/format contract, distinct video-link counting, and continued independent QA. High-stakes and software-version gates remain.
- A follow-up supplies YouTube-verified titles, creators and canonical links for AI watchlists, using bounded public searches and metadata retrieval. It does not infer dates, playback or technical accuracy. The gate rejects selected links outside the verified candidate set.
- Scout's request/reference data and Athena's draft are clearly separated. Athena no longer receives trailing generic audit instructions that she can mistake for part of the draft.

## Verification

- Thirty initial regression checks passed; the final suite passed all 35 checks, covering prior software/high-stakes behavior, transport recovery, prompt boundaries, video identity/deduplication, metadata failure, exclusions and public-query privacy.
- The first canary correctly finished PARTIAL when it exposed placeholder links, guessed metadata and the QA-boundary defect. Those findings led to the follow-up, rather than a premature completion claim.
- The final fresh production task completed with three distinct supported video links, exact titles/creators and Athena APPROVED. Scout session: 20260917_151547_16bb81. Athena session: 20260917_151604_f9568b. Task: 0cf7a763-1918-46df-a52b-b583eb6b702f.
- No Kanban calls and zero outbound delivery receipts in the final internal test. Bridge and task service health checks passed; deployed hashes matched the tested files.
- The final picks concern Hermes production use, agent concepts and a practical quickstart. Video metadata/descriptions were checked; full playback and subjective entertainment quality were not independently verified.

## Review exception — this task only

The initial applied revision received completed Claude review in session 20260917_145404_848a0d. Initial revision manifest SHA-256: 26a8245374bcc08f9490872e4f435ee0b306eee3200a75a08bb467cf7e42fa09.

Claude's follow-up review became unavailable through provider credit and credential errors. William then explicitly stated: "If claude is unavailable, you may skip this task’s review requirement". The final follow-up was tested and deployed under that task-specific exception. This is not a standing exemption and does not change CLAUDE_MANDATORY_REVIEW.md for other work.

## Use, limits and recovery

Fresh staff assignments automatically load the repaired runner, metadata collector and search provider. William can ask normally for entertaining agentic AI videos relevant to the existing setup; no special command or extra tracking step is required. Existing gateway processes may retain older imports until their normal restart. No old tasks were replayed and no pending queue was swept.

The metadata collector uses a small set of public searches for the existing AI setup and may miss newer or differently described videos. It provides candidates, not an exhaustive watchlist. Dates remain unverified unless separately established. Keep stronger evidence standards for high-stakes recommendations.

Detailed source, tests, exception, review and rollback evidence remain in local operator packets staff-repair-20260917 and staff-watchlist-20260917. The former holds the initial repair/backups; the latter holds the final follow-up and successful verification receipt. Roll back in reverse deployment order using the packet procedures and drift/idle checks. Preserve and retest the search-provider patch during future Hermes upgrades. No model/provider upgrade or unrelated system change occurred.

## Publication boundary

Live repository metadata reported the established backup repository PUBLIC, contrary to earlier descriptions of it as private. Only sanitized operating notes are added to shared context; detailed source/review packets stay local. No repository visibility or permissions were changed.
