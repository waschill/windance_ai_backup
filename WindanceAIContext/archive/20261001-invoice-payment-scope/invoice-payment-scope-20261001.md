# Invoice payment-state scope — October 1, 2026, 08:18 UTC

Outcome: payment-state interpretation advanced and the staged formatter now labels its scope accurately. Production remains unchanged. Phase 1 and natural delivery acceptance remain open.

## Evidence and interpretation

Live SaaS field metadata distinguishes Not Paid, Partially Paid, In Payment and Paid. A bounded metadata inspection found 64 posted In Payment invoices with positive residual, 65 linked payment records, no unreadable linked payment IDs and no invoice lacking matched payments. All 65 payment records have state paid; 64 lack a journal-entry link and none have is_matched=true. Every examined invoice has at least one matched payment with no journal entry and state paid/in_process. All 64 also expose reconciled_payment_ids, demonstrating why that relation name alone cannot establish bank settlement. No invoice identity, amount, customer, bank detail or report body was exported.

Odoo's public 19.0 source explains that positive-residual invoices can enter the In Payment path when matched payments have no journal entry and state in_process or paid. This is consistent with the observed metadata. It is an inference from the public implementation, not verification that SaaS 19.3 runs that exact source revision. Bank settlement, payment correctness and bookkeeping configuration were not audited. Do not treat these 64 invoices as proven collectible debt or silently mark them paid. [Odoo account.move source](https://github.com/odoo/odoo/blob/19.0/addons/account/models/account_move.py#L1238-L1244).

Official documentation pages timed out when opened; they were not used as evidence of tenant behavior. Public source and actual read-only tenant metadata supply the bounded explanation above.

## Staged correction

Preserve the existing posted/customer-invoice/positive-residual/not_paid-or-partial filter. Change the report heading to name those states. Both nonempty and empty successful reports explicitly exclude In Payment invoices and state that the report does not verify bank settlement or authorize collection messages. An empty selection must not claim all customer balances are settled. No additional payment reads are introduced into the proposed scheduled formatter.

Seventeen synthetic tests passed on HERALD's real Harness interpreter in the existing isolated workspace, including new tests for explicit scope on empty/nonempty results and rejecting an unexpected In Payment row. Query, classifier, failure, currency, decimal, cap and fake-sender tests also passed. These are no-I/O fixtures; no Harness application was imported, real report sent, schedule triggered or service restarted. The previous 11-row live formatter comparison applies to the earlier candidate; this revision changes wording, and a fresh final staged diff/read-only preview remains required before installation.

The revised packet is archived with all test fixtures. Prior packets remain historical. No production rollback is needed for this checkpoint. Existing verified private recovery points remain authoritative. Before production installation, rebase only the formatter and SAL get_report function against live source, preserving the already-installed recipient resolver; check maintenance ownership, fresh recovery and source equality; retain no-send preview and natural-delivery gates. Do not overwrite the full SAL script with the older pre-recipient snapshot.

## Limits and next step

Four successful read-only Odoo requests were made this checkpoint: invoice schema, payment schema, invoice linkage, and payment metadata. No application model call, purchase, new paid commitment or accounting write occurred. Codex cost remains unmeasured. SAM stayed untouched, Warden checks remain suspended, and the separate alarm-link repair still requires the requested owner approval.

Next bounded implementation step: prepare the exact combined invoice deployment diff and fresh recovery/preflight evidence. No need to broaden the unpaid filter to the 64 In Payment invoices to correct formatting. Any payment-reconciliation investigation or collection workflow is separate from this operational report and remains unperformed.
