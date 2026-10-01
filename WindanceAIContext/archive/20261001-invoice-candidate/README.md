# Unpaid-invoice correction candidate — NOT DEPLOYED

Prepared October1 UTC / September30 Mountain during Phase1 baseline completeness work.

## Problem and resulting behavior

Live Harness grouped by customer display name and added balances across currencies, omitted invoice identifiers from rendered lines, and could borrow an original total from another row with the same invoice name. SAL's scheduled wrapper ignored the returned query classification, permitting an Odoo error string to look like a successful normal report.

The proposed replacement preserves the read-only posted/unpaid invoice query and caps it at1000records. It groups balances by currency identity, uses customer IDs for counts, renders each row's own invoice ID/name, original total and remaining balance, uses Decimal arithmetic, and retains returned fractional precision. Missing/invalid money, currency, date or duplicate identity fails closed. A capped result explicitly says totals cover only displayed records.

The SAL get_report replacement checks both result kind and source before printing report text. Existing main handles failure with exit1 and its existing alert route; no recipient, schedule, approval policy or transport changes. Error details from Odoo are not copied into the normal report.

## Contents and boundaries

- invoice_function.py: replacement function only, not a standalone service.
- sender_function.py: replacement SAL get_report only.
- harness-original.json / sender-original.json: extracted original functions, paths and whole-source SHA256 values. No credentials or recipient literals included.
- main-original.json: unchanged scheduled entrypoint used with fake send/alert adapters in testing.
- test_invoice_candidate.py: synthetic query stub and encoded-query execution with in-memory import stub; no real Harness import, Odoo access, database, SSH subprocess, sender, scheduler or dispatch.

15 tests passed on HAL's available Python and HERALD's actual Harness service venv. The HERALD isolated directory is /Users/herald/forge-workspace/agentic-invoice-isolated-20261001. Checks cover read-only query contract/cap, separate currencies, duplicate display names/invoice numbers, partial balances, decimals, missing data, capped totals, successful empty results versus errors, wrapper classification and actual main failure/success routing through fake adapters. This is not a live invoice data reconciliation, actual send, full app restore, restart or natural scheduled-delivery test.

Live applicability remains unverified: the actual tenant may use only one currency; mixed-currency fixtures establish a code defect, not a demonstrated incorrect real balance. The scheduled failure's cause is also not established by these fixtures. Numeric values returned as binary floats have already lost any upstream precision before this function sees them; Decimal(str(value)) avoids introducing additional float aggregation error but cannot recover lost source precision.

## Guarded deployment and recovery plan

No production change is authorized merely by this packet existing. Within the approved project, first complete the relevant baseline/recovery gate and coordinate the distinct held Harness repair. Preserve Warden's explicit held-repair/consensus requirements.

1. Re-read live source hashes; require equality with the source hashes in the original JSON records. If changed, stop and reconcile the actual diff, then rerun relevant tests. Do not overwrite the later Odoo JSON2 migration or other user changes.
2. Establish a fresh private exact source restore point for both files after a credential/privacy scan, plus service definition fingerprints and appropriate application recovery evidence. The fresh selective backup contains Harness source; the SAL sender requires its own current restore point before modification. Existing backups are not proof of a complete application restore.
3. Pause Warden and confirm quiescence for any coordinated service maintenance. Inspect active tasks, live requests and maintenance ownership. Replace only the two named function spans, preserving all other bytes/settings where practical; verify expected AST and source diff before any restart.
4. Run isolated tests against the actual staged spans. Perform a read-only, no-send preview when permitted and compare independently with Odoo source data privately; disclose scope and truncation, not raw customer data in shared context.
5. Restart only the affected Harness if needed under the separately applicable maintenance authority. The SAL command is invoked per scheduled run and needs no scheduler change. Recheck health, task state and owner/recipient guards. Never replay an earlier invoice report to manufacture delivery evidence.
6. Verify the next natural run separately: exit status, report identity, exact intended recipient, independent receipt and absence of duplicates. Record proof and limits before declaring the workflow reliable.

Rollback is a selective restoration of the two saved function/source revisions only after ensuring no newer changes would be lost, followed by scoped service verification. Do not restore an entire live database, replay tasks, enable the phone or change Odoo data. A decision to roll back must preserve the same Warden and maintenance boundaries as deployment.
