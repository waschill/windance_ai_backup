# Memory ownership and attribution baseline — October 1, 23:34 UTC

Read-only metadata and isolated current-code tests identify two separate problems. No private conversation, mailbox or counselor body was exported or supplied to a model. No production memory was edited or reindexed. Phase1 privacy acceptance remains open.

## Retrieval boundary reproduced

The installed vector_recall function selects up to500 most recent vector rows without owner filtering; relevant_memory_text falls back to unscoped memories_text when retrieval has no usable result. The email request-owner context added in the preceding repair does not cover these functions.

AST-extracted current functions were executed against a temporary SQLite database containing only two synthetic conversation records, one per owner. Both semantic scoring and lexical fallback returned both records for each scoped owner: four cross-owner cases. An empty retrieval also reached the unscoped fallback under Shawn's context. No real embeddings or model calls were made. The first test attempt omitted the Any annotation binding and failed before execution; after supplying that test dependency, all reproduction assertions passed. This is evidence of a missing filter, not proof that an actual historical private message was disclosed.

## Authoritative metadata map

At inspection, vector_memory contains1570 records:854conversation,677memory,36staff_task,3ops_item. Its schema contains source_type/source_id but no owner or business/personal access scope. The separate memories table has678records and a source field but no explicit owner/access scope. Conversations retain884rows with user attribution:809William,10Shawn,65other. No content was inspected to produce those counts.

All854conversation vectors join an existing conversation source row:779William,10Shawn,65other. No conversation orphan was found. **All10Shawn conversation vectors have a William: prefix in their stored text**, as measured by a count-only predicate. Current message insertion and reindex code hard-code William into that prefix instead of using the source user. This can misattribute remembered statements even apart from access control. Source user metadata is the evidence for correction; the prefix/title must not be trusted as an ownership label.

All36staff-task vectors join tasks whose requester is William. The677memory vectors join source memories using the actual kind:key composite key. An initial integer-ID join returned zero and was corrected after source inspection; it was not evidence of orphaned memories. No memory rows have an empty source field, but a nonempty source string alone does not prove ownership or permission to share. The65other conversation sources, legacy memory facts and three operations vectors need explicit scope treatment rather than guessed attribution.

## Required correction and gates

1. Filter retrieval using authoritative source ownership before ranking/limit, consistently across semantic and lexical paths. Test both directions, unknown owners, orphaned sources and concurrency. Preserve the source pointer in returned evidence. Do not filter solely by text/title prefixes.
2. Eliminate unscoped fallback for owner-scoped requests. Retain existing records; withhold entries lacking verified access metadata until classified. Do not silently label all legacy facts as William's or shared business information.
3. Introduce correctable owner and business/personal scope metadata for new learned facts and shared business sources, with explicit provenance and a way to amend/revoke access. Trace all write/retrieval paths including direct API/tool callers before calling this enforced privacy.
4. Correct future conversation attribution using the source user. Prepare a narrowly guarded correction of the10verified mislabeled derived entries, preserving originals and their source conversations; do not bulk reindex or overwrite historical records to hide the defect. Unknown ownership remains unknown.
5. Verify source-aware memory correction/deletion propagates to derived retrieval indexes. The previously discovered invalid high-confidence training snapshot remains preserved and separately unresolved.

These requirements are within the approved source-backed, correctable, separated memory goal. They are not yet implemented. The mailbox capability guard stays in place and should not be portrayed as solving memory or privileged tool isolation. The next step is an isolated owner/scope retrieval candidate and migration/readback plan, not an indiscriminate rewrite of the knowledge base.

Recovery: nothing changed in production in this work unit; preserve current private backups and failure evidence. No paid commitment, new installation or application model call; Codex cost remains unmeasured. Warden stays suspended, phone disabled, SAM unchanged, and the approved alarm restoration remains blocked by browser access policy.
