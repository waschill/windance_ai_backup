# Numbered selection integrated in staged Harness

October 2 UTC / October 1 Mountain 2026. No production change; Phase 1 open.

Full private candidate now installs the selection evidence table through actual db initialization and invokes atomic selection claim from process_numbered_gmail_pin_decisions. Existing PIN decision parsing, duplicate-number rejection, report-reference membership and freshness checks remain. Explicit William-mail capability guard precedes parsing. Separate child creation and unconditional original rejection are replaced by the single transaction. Selected execution writes executed or uncertain only from executing, verifies exactly one final receipt row, and suppresses raw provider error content.

Five actual-schema/handler tests pass: competing calls execute one intercepted batch and create one remainder; lost result persists uncertain and one remainder; mocked failed PIN and missing reference cause zero execution/children; rejection-only preserves remaining items without executing. Child keeps original request time and explicit expiry. Actual parser and reference checks ran; PIN matching and mailbox executor were intercepted, so this is not an end-to-end authentication or send test. No real approval or mailbox data used.

Private package `/Users/herald/backups/email-selection-harness-20261002`:

- Main `c4b45ee3cefa7b28667b9316854a3d5400b886a9479333bded6a34d62c78b9d0`
- Selection helper `002851f11cb1e24b30b0c9a81dfa1a9d20bb1502ce26cabc0dd04d5786358c5f`
- Intent helper `1921745a84f26299cc3e5a70645d8b83ea9ec317ecf298c022e8fff0f75244c3`
- Draft recovery helper `4ae40da14bf033af295c68f5e30c8e940284963598d3ac22d42e3036ec848c51`

Builder modifies only schema and numbered selection handler relative to pinned r2 whole-claim source. It preserves unrelated AST and all earlier staged recovery code.

Remaining: stable per-item execution identity/partial batch outcomes, shared mailbox holds across approved/autonomous/undo paths, correct remainder display, real authentication/account binding, transport bounds, status visibility and authoritative reconciliation. Selected success audit currently occurs before final receipt persistence; audit alone must not prove committed success. Actual process-death tests for whole claims do not certify this selection branch. Fresh full startup/private/off-host recovery must include the third table and new helper for this exact revision. No deployment until these gates are satisfied.

Retain private candidates/backups; no live rollback needed. Never reset uncertain/executing records on time alone or replace live databases with stale pending approvals. No Gmail/model/Odoo/send calls, service/SAM/Warden/phone changes or new charges. Codex account capacity is consumed; dollar attribution remains unknown.
