# Source-owned memory retrieval candidate — October 1, 2026

Status: staged and tested only. Production remains on the previously deployed email-owner guard; no memory row or retrieval code was changed live. This is an intermediate privacy correction, not full adaptive-memory acceptance.

## Candidate behavior

The candidate selects conversation records by their joined conversations.user and staff-task records by joined staff_tasks.requester, before ranking or the500-row candidate limit. Unknown identities, orphaned sources, title-based ownership claims and unclassified legacy facts are withheld. Existing records remain untouched. No implicit grant of shared-business access is introduced.

Returned text is reconstructed from the current authoritative source, retaining source type/ID and owner/private access metadata. A stale or mislabeled derived text cannot substitute old words for an edited source. Its stale embedding is not reused; lexical matching remains available. Future conversation insert/reindex code uses the actual source user instead of the hard-coded William label. The ten existing mislabeled derived entries are not rewritten by this candidate; corrected source attribution is projected during retrieval.

The staged Harness integration reads identity from the request-local context, protects both semantic and lexical paths, requires verified owner identity before retrieval, and replaces the unscoped fallback with the same source-filtered selection. A private helper adds a read-only current_request_owner accessor. The existing William-owned Second Brain branch is not enabled for Shawn without verified library-access rules. Direct tools and service calls without a bound identity do not acquire private memory by default in this candidate.

## Verified tests

Eleven synthetic policy tests passed on HAL and HERALD's application Python: bidirectional exclusion, unknown identity rejection, owner filtering before a501-foreign-row flood and limit1, orphan/unclassified exclusion, source-based correction of a false owner prefix, current-source text after correction, deletion/owner-change revocation, retaining a matching embedding, task requester authority, and unchanged source/derived tables.

AST-extracted candidate integration passed four owner/mode cases, absent-scope withholding, both empty-search and embedding-error fallback checks, unknown-legacy exclusion and a source-correction check without reindexing. These tests use synthetic embeddings and records only. They establish no stale private text is returned in the exercised cases, not guaranteed semantic discovery after every source edit; stale embeddings may reduce ranking coverage until refreshed. No actual source deletion, correction or sharing grant was applied in production.

## Deployment gates — not yet satisfied

- New learned facts currently use an unscoped legacy writer. Bind new writes to explicit owner and scope with durable provenance and correction/revocation metadata. Ensure the service cannot say a fact is learned while silently making it unretrievable. Preserve per-owner keys so two users cannot overwrite each other's similarly named facts.
- Classify legacy facts from trustworthy sources without guessing from prose, title or a merely nonempty source string. At the current metadata checkpoint,825vectors have recognized conversation/task owner provenance before per-query limits;745others comprise677legacy-memory,65other-user-conversation and3operations vectors. They are retained, not deleted. These counts are not classification decisions.
- Add explicit business/personal and private/shared grants with authorization and audit history; do not turn all business-sounding facts into shared knowledge. Protect direct API/tool identity separately from a caller-provided owner string.
- Trace all background and direct-tool callers affected by identity-required retrieval, preserve the installed mailbox guard, and test real adapter integration with no private external prompts. Perform fresh backup/cold/off-host checks and verify whole-source diff and current maintenance state before any installation.
- Correct the ten known derived attribution defects only through a guarded reversible procedure retaining original evidence and validating source links. Source projection here does not claim stored-data repair or re-embedding.

No database schema migration or original-memory rewrite is part of this staged packet. The next work unit should implement/test owned-fact write and readback semantics, then assess the combined migration rather than installing an incomplete reader-only solution.

## Paths, hashes and recovery

Private candidate on HERALD: /Users/herald/services/memory-owner-boundary-20261001. Candidate Harness SHA256 fcd6002aa610650f9529ea1e1f41d7fedd869a49d57ae493868005c38594e157, based on deployed db8a435907a2fb49796818a17b29334874b1919d6a03640901a22b6b12ea8195. Candidate email context helper SHA256 ae79c4ca68f17e4297f89075e2ecb02a0b06f268c43668d621290bafe8542b43. Full private Harness source stays out of the archive; reproducible source guard/builder, small new selector, tests and sanitized receipt are archived.

No production change means no rollback is needed. Do not replace the live helper/source with this incomplete packet. Future source changes must rebase it. Existing guarded email capability fix remains active. No model/embedding calls, paid commitments, sends, Odoo/SAM/Warden changes or browser-policy bypass occurred. Codex dollar cost remains unmeasured. Phase1 and the broader memory/interface/job gates remain open.
