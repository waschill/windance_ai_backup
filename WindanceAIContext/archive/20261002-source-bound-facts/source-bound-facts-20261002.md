# Private memory source binding

October 2 UTC / October 1 Mountain 2026. Staged component, not deployed.

Previous request-ledger tests prove an authenticated adapter requested a write and retries are stable. They do not prove that its value came from the referenced owner message. The new server-side seam reads a source through an injected trusted loader, checks owner/channel/reference and exact excerpt containment, validates content, and atomically records the fact/request plus source and excerpt hashes. The assertion is explicitly a **source_quote**, not externally verified truth or proof of the owner's belief: an owner message can itself quote third-party material.

The manager-source loader reads only owner/channel/request for an exact retained message ID through a read-only connection. Source bodies are not copied into the provenance table. This does not fix manager ingress authentication: the manager currently accepts an owner claim/default from trusted callers, so production deployment still requires authenticating that upstream identity and determining that the request authorizes remembering/correcting the cited content. Source text is data, never new execution authority.

Source binding, fact mutation and replay receipt commit together in the fact database. Provenance participates in the idempotency fingerprint, so changing source context cannot reuse the same event as if it were unchanged. A changed source detected before commit rolls everything back. Source storage is separate, so this is not a distributed atomic transaction; retrieval rechecks its current hash and withholds a deleted, changed, missing or mismatched source. Correction can create a new source-bound fact revision. No derived embedding or shared Hermes copy is written.

Ten new cases plus37existing component tests pass (47total): source/receipt atomicity, exact replay, invented excerpt, wrong owner, source drift and correction, changed-source event conflict, injected provenance-write failure, source change during commit, rejected content, deleted/missing source, authentication before source lookup and actual manager-schema owner comparison. Some cases group multiple assertions. Tests use in-memory/disposable SQLite and synthetic statements; no real source bodies, production database, model calls or external I/O.

`source_fact_gateway.py` gains optional provenance in its fingerprint and an explicit joined-transaction seam. Existing calls without provenance retain the prior fingerprint shape. The new `owned_fact_sources` table is installed only by explicit invocation; no live schema was changed.

## Remaining integration and privacy gates

Authenticated intake and source authority; user-facing remember/correct/forget and source-selection behavior; HTTP/worker integration; source correction/revocation lifecycle across sessions; legacy writer/retrieval/mirror migration; and explicit hypotheses for inferred habits remain unfinished. This exact-excerpt seam does not yet accept paraphrases or infer habits. Cross-owner source retrieval is deliberately withheld even if a business fact has a grant until a source-redaction/sharing policy is implemented; existing fact-store sharing tests are not proof this new reader supports shared-source answers. No whole-stack memory acceptance is claimed.

No production changes or new cost commitments; zero application model calls, Codex cost unknown. All SAM, Odoo, Warden suspension, phone, SyncThing and Level 8 boundaries unchanged. Phase1 open.
