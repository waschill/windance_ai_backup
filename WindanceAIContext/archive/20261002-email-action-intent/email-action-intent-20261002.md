# Durable autonomous email action intent, staged

October 2 UTC / October 1 Mountain 2026. Not installed.

The staged journal commits an unconfirmed operation before an autonomous Trash or unsent-draft callback. The operation key hashes William plus mailbox message ID, so changing action type cannot silently create another action for the same message. A request hash binds action and payload; mismatches hold. Confirmed receipts can be reused without a second effect; unconfirmed operations never expire or reset automatically. The journal stores hashes and minimal receipt identifiers, not subjects, recipients, message bodies or draft content. This fixed service scope is not authentication of a human sender.

Three real child exits were tested with temporary SQLite and a fsynced synthetic effect file: before callback effect, after accepted effect/before confirmation, and after durable confirmation. Restart held the first two and reused the third. A competing process held while the first retained its claim; only one synthetic effect occurred. SQLite integrity passed. These are journal-level process/concurrency tests, not full Harness process recovery or Gmail acceptance evidence.

The private composed full source adds the journal table to actual db schema and wraps the two autonomy-report mailbox calls while retaining the earlier truthful-outcome correction. Every other top-level definition is AST-preserved relative to that staged correction. Candidate SHA365299e32e4d65626db2d1f277f450bd37c4f89bffaba3beebaa275770c3b192; journal SHA00f0ab858ed876ef8525ebda8971191f4db023d770d0b3d1cbdd6efe4da3f5c0. Private directory: `/Users/herald/backups/email-intent-candidate-20261002`. Full source remains private.

Six baseline/six candidate report scenarios were rerun with the composed actual report function, synthetic adapters and fixture journal schema. Lost/malformed receipts record uncertainty; normal receipts remain compatible; preparation failures attempt no effect. This does not yet run the full actual database initialization or module startup. The unchanged live seed_memories function commits its own inserts before db returns, checked to avoid mistaking an already-open transaction for journal compatibility. Full schema/recovery validation is still required.

## Remaining work and limits

Compose actual schema/startup with pre-existing private data, test full report interruption/local receipt failures, and expose held operations for review even when the original message leaves the inbox. Draft payload includes generated body in its request hash: changed regeneration will hold rather than silently accept a different action. Avoid unnecessary repeat generation by consulting a stable recorded request before invoking the model in the next integration step. Existing legacy handled-message rows and explicit sender-rule/direct approved handlers are separate and must be reconciled; this does not protect every Gmail entry point.

Authoritative reconciliation needs evidence for the exact operation; a current label, missing inbox item or matching draft text alone cannot justify retry or resetting a hold. Older database restoration must not erase intents created after the snapshot. No delete/release API or automatic retry exists. Staged files need no production rollback. Before deployment verify backups, exact source/helper identities, current maintenance ownership/idle state and preserved records; never replay a real mailbox report as a test.

Zero actual mailbox/model/send/dispatch calls and no live schema changes. Source remains deployed batch guard0a95a09...; this candidate includes additional work not live. Application model usage zero; Codex cost unknown. Phase1 remains open. SAM/Odoo design, Node-RED access hold and all protected rules unchanged.
