# Explicit source-intent memory HTTP integration

October 2 UTC / October 1 Mountain 2026. Candidate mounted only on an actual Harness app in a disposable process; production unchanged.

`source_memory_api.py` adds staged `/memory/owned/from-message` and `/memory/owned/source-query` routes. The write request supplies owner/channel/scope/source reference, not a free-form value, key or target revision. Scoped authentication happens before source lookup. Server reads the retained owner message, requires an explicit remember intent, derives its value and stable record/event identity, then uses the atomic source-bound gateway. Extra caller fields are rejected. The route creates an initial memory; it cannot overwrite a caller-selected existing fact.

Ordinary recognized remember requests default to personal scope. `Remember for business: ...` and `Remember for personal: ...` explicitly select scope; a leading Vega address is accepted. Caller scope must match the parsed source intent. Business classification does not grant another person access. Quoted instructions embedded in a narrative do not qualify as a top-level remember request. Stored material remains a source quote, not automatically verified external truth or a claim that every statement in a quoted document is the owner's belief.

Actual current Harness imports, middleware and HTTP routing were exercised with disposable Harness/fact/source databases, synthetic credentials and intercepted external operations. Checks passed for missing credential, forged owner, same-source replay, caller value override, scope mismatch, quoted instruction, secret-like content, explicit business capture, exact owner read, cross-owner withholding, source-change withholding and conflicting source replay. Two synthetic facts persisted; no production data, model inference, sends or task dispatch. Existing installed Harness private-memory guard was retained. Final test includes `Vega, remember for business` addressing.

Private test directory: `/Users/herald/services/source-memory-http-20261002`. No production route was mounted and no production credential or schema provisioned. This is in-process ASGI with synthetic sources, not a natural Messages-to-memory acceptance run.

## Still required for complete learning

The actual manager/SAL source identity must be authenticated before relying on its owner claim; production caller credentials and transport must be provisioned with least necessary scope. Current manager trusted/local caller defaults do not prove person identity. Bind the conversational request to the retained source reference and provide an accurate source/record receipt. Corrections and forgetting need explicit target/source intent, durable revision conflict handling and truthful acknowledgments. This initial-write route deliberately does not replace those requirements. Sharing/source redaction, inferred habits, legacy writes/readers/mirrors and source-retention policy remain open. Do not deploy an incomplete reader-only migration or silently break existing callers.

No production change, model route change, paid commitment or application model call. Codex cost unknown. SAM, Warden suspension, Odoo, SyncThing, disabled Level 8 and phone rules preserved. Phase1 open.
