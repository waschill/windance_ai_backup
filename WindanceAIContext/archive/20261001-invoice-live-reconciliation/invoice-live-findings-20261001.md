# Live invoice reconciliation — October 1, 2026, 06:19 UTC

Phase 1 evidence checkpoint only. Production formatter remains unchanged; no report was sent, no Odoo record was mutated, no scheduler/service was started or restarted, and SAM was untouched during its protected interval. The separate alarm-link approval remains pending; Warden checks remain suspended by owner direction.

## What passed

On HERALD, the existing JSON-2 adapter read posted customer invoices classified not_paid/partial with positive residual. A count and capped detail query agreed on 11 invoices, one currency and zero partial invoices. The staged formatter ran against an in-memory frozen copy; all invoice numbers, row-local original totals, residuals and due dates matched the source projection, and its currency total matched a separate Decimal calculation. Repeating the candidate on that same frozen snapshot produced the same output. Invoice/customer identities, amounts, report bodies and credentials were not exported or persisted by the probe.

The live old function, extracted without importing the Harness application, returned deterministic classification on the same rows but omitted every invoice number. This confirms the identifier omission on actual data. Mixed-currency and partial-payment corrections remain covered by earlier synthetic fixtures, not this live snapshot.

Current Harness source SHA256 is still `709118f2ae2bf9df5d429e1343c06d709707f8f422db54058085801fca0e3aa7`; staged invoice-function SHA256 is `c267f4042698dc93d34324beb013369e1987a7ec01ba25c4e02e30028a01b21a`. SAL's helper remains the approved installed recipient revision `e97253109a085b974c917965c8213a617c8ced7a01741f014162ea09da8f529e`; this does not install the separate invoice formatter or classification fix.

## Coverage finding — unresolved report semantics

A second, broader projection read all posted customer invoices with positive residual, omitting the payment-state restriction. It returned 75 invoices, below its 1001-row limit. The additional 64 are classified **in_payment**. Therefore the current 11-row report is not a complete inventory of all positive residuals. This is an intentional query-filter difference observed live, not proof that Odoo is wrong or that those 64 invoices should be collected. Their payment/reconciliation state needs a distinct label and business interpretation before any broader report or reminder workflow is accepted.

The probe marks overall coverage incomplete because the independent broader projection differs. The candidate passed the selected 11-row formatting checks; do not misreport this as a formatter failure or as complete unpaid-invoice acceptance. No filter was changed. Next bounded step: inspect read-only payment-state semantics and prepare a clear distinction between not_paid/partial and in_payment, with no collection actions or recipient changes. Do not equate in_payment with collectible debt.

## Failures and corrected interpretations

An initial server aggregation attempt using read_group failed locally with ValueError because the existing JSON-2 adapter has no positional-argument mapping for that method. This was an unsupported argument mapping, not a remote Odoo failure or a reason to relax connector protections. The initial receipt is retained. The final probe uses only already-supported search_count/search_read methods, with three bounded reads and an independent broader projection. Reads are sequential, not a transactional snapshot; concurrent business changes remain a limitation.

The invoice LaunchAgent is registered once on SAL at gui/501/com.windance.ledger-unpaid-invoices, pointing at the normal `.plist` with 08:10 schedule. A glob initially matched a historical `.bak` carrying the same label and old 08:00 time. The second receipt disambiguates the backup from the actual loaded registration; there are not two verified invoice jobs. Last recorded exit is still 1, and retained log timestamps precede the recipient correction. The historical failure cause and next natural delivery remain unproven. Logs were reduced to types/timestamps; raw log bodies were not exported.

The HERALD task-inbox file says no pending bridge work but is dated August 12; it is stale and cannot establish current maintenance ownership. No service mutation was attempted based on it.

## Evidence and recovery

Receipts: invoice-live-reconciliation-first-attempt-20261001.json, invoice-live-reconciliation-20261001.json, invoice-runtime-check-20261001.json, invoice-schedule-reconciliation-20261001.json. Reproduction: invoice_live_reconcile.py against the staged invoice_function.py on HERALD. It imports only the existing JSON-2 adapter, extracts the old function with AST, substitutes frozen rows for both formatters, allows at most three reads in the final revision, and prints sanitized metadata only. Do not execute the scheduled sender as a test.

No production rollback is needed because this checkpoint changed no production file or business data. The staged candidate copy under `/Users/herald/forge-workspace/agentic-invoice-isolated-20261001` remains outside service directories. Existing recovery points and the alarm hold are unchanged.

This work made five successful read-only Odoo calls across the initial and corrected probes, plus one locally rejected mapping attempt. Final query times were 1127, 1122 and 1047 ms; these are individual observations, not p50/p95 or delivery latency. No application model calls, software purchase or paid commitment occurred. Codex usage and total dollar cost are not measured. No phase or natural-delivery gate passed.
