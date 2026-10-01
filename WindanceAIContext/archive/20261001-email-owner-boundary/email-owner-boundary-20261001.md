# Email acceptance: reference integrity passes; internal owner boundary fails

October1, after service recovery. Phase1 remains open. No real mailbox content, identifiers, counselor data or secrets were exported; no live mailbox action or message send occurred.

## Verified current reference state

Read-only application-runtime inspection at23:16UTC found the active William report has five references, all contiguous with nonempty unique message IDs and matching expected count, dated23:00:27UTC October1. Historical reference count109 and autonomy action count146 establish current metadata only, not successful delivery or owner approval of every action. No private IDs or subjects were output.

All14 archived snapshot tests were rerun against AST-extracted current production functions using temporary SQLite fixtures and fake Gmail/action/approval adapters. They passed, covering missing/corrupt/incomplete maps, no older-map fallback, changing inbox order, mixed invalid batches, replacement/empty snapshots and retained approval requirements. A source parsing DeprecationWarning about an unrelated escape sequence was observed; no production change was made for it. These tests do not prove owner isolation.

## Reproduced owner-boundary defect

The actual Harness HTTP handler was loaded in a separate process with disposable DATA/CONFIG/LOG and Google-config paths. Network and subprocess effects, models and staff dispatch were denied. A single synthetic saved reference represented William's report; request_approval was a recording stub, not a real approval or mailbox operation.

Both user=William and user=Shawn requests to /message with channel=vega-internal and text delete1 (with the normal separating space) returned deterministic/gmail-summary-actions and invoked the approval stub with that same synthetic William message ID. Thus the internal handler's recorded owner does not prevent preparing an action against William's global active snapshot. The retained test uses the exact text and source interface. No approval was exercised and no actual email was read or deleted.

The initial Check my email fixture was inconclusive: denied embedding/planner calls resulted in generic error before the synthetic summarizer. It was not counted as proof of privacy. The narrowed delete1 fixture reproduced a concrete boundary crossing without inference or mailbox I/O. The final receipt distinguishes preparation from mailbox-handler execution: approval_prepared=true for both owners, mailbox_handler_called=false.

This does not prove that any real Shawn request accessed or changed William's mailbox. Existing sender-aware manager sessions and fixed recipients remain useful controls, but do not by themselves enforce ownership in downstream legacy email handlers. A caller-provided owner and synthetic session separation are not sufficient evidence for the overall privacy gate.

## Required focused correction

Add and test a deterministic owner boundary before any shared William-mail report, numbered action or approval handler executes. Preserve William's existing report references and standing approvals. Route Shawn only through her separately scoped mail service; ambiguous/unavailable owner routing must withhold, never fall back to William. Inspect all shared approval entry points and direct internal tool routes so a fix to this one phrase is not mistaken for complete coverage. Preserve non-email Odoo/training functionality and actual owner identity from intake. Do not deploy broad service shutdowns or rewrite current reference tables as a workaround.

The correction is not prepared or installed in this work unit. Prioritize it before accepting sender-separated email operation. Use synthetic cross-owner fixtures, whole-batch rejection tests and explicit spies for reads, draft/delete/rule changes and sends. Real mailbox action is unnecessary to prove rejection. No privacy-boundary pass is claimed.

Recovery: no production mutation here. Test state was confined to automatically removed temporary directories; preserve the archived sanitized test/receipt as failure evidence. Existing service recovery backups remain valid for their respective checkpoints; do not overwrite newer live records.

Costs: zero application model calls and paid commitments for this diagnostic step. Codex usage and dollar attribution remain unmeasured. Warden remains suspended; SAM, SyncThing, Level8, phone and browser-blocked alarm repair unchanged.
