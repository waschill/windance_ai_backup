# Windance cost baseline and planning estimates

This is a measured usage baseline plus explicit planning assumptions, not a reconciled bill or a quote for another architecture. No paid provider generation or staff work was initiated by the audit scripts. This Codex audit session and the existing production activity still consume their normal capacity; publication uses existing local indexing/embeddings.

## Available recent usage evidence

Read-only aggregates from the nine operational profile session databases cover sessions started within the rolling seven-day window at approximately September 30 06:00 UTC. Counselor/private reviewer stores were excluded. Sessions begun earlier, manager Codex app-server turns, this HAL session and other providers can be outside this aggregate.

| Measure | Observed |
|---|---:|
| Session rows | 222 |
| Rows labelled subscription included | 160 |
| Rows without billing status | 62 |
| Recorded API calls | 671 |
| Recorded input tokens | 4,713,231 |
| Recorded output tokens | 333,926 |
| Recorded cache-read tokens | 12,352,000 |
| Estimated metered cost on included rows | $0 |
| Rows with reconciled actual cost | 0 |

The 62 unattributed rows show zero recorded calls/tokens in this extraction, including older local-model session records. That does not prove they consumed no resources. Cached/input accounting has not been reconciled against provider definitions; do not add these fields and price them as an invoice. The measured subscription-included rows reflect recent Terra/Codex OAuth work. Their zero metered estimate means the client classified it as included, not that the subscription or entire stack is free.

## Current monthly cost estimate

The honest current formula is:

`existing subscription allocation + separately billed providers/search/extraction + phone rental/usage + electricity + storage/hardware allocation`.

The existing subscription charge and limits, any purchased credits, OpenRouter/private review bill, Brave/Tavily/browser/image/transcription charges, Telnyx rental and power tariff were not available in the inspected operational records. Phone disablement does not cancel number rental. There is no defensible single total until those amounts are reconciled.

For planning only, assume the relevant always-on compute draws 200–600 W in total and electricity costs $0.15/kWh. At 720 hours/month that is 144–432 kWh, or **$21.60–$64.80/month**. This is a scenario, not a wall-meter reading or a verified local tariff. It excludes NAS/monitors/network power unless included in the assumed wattage. Existing equipment requires **$0 new hardware procurement for this baseline**; depreciation/replacement is not zero and is unpriced.

Under current included subscription treatment, the 160 classified sessions estimate **$0 additional per-token charges**, subject to the actual plan/quota and any purchased-credit use. Do not extrapolate that into unlimited capacity. The current stack's total is therefore **unverified subscription and external charges, plus the illustrative $21.60–$64.80 power allowance**.

## Three-pilot resource budget

These are planning allowances for one isolated pass, not measured execution or authorization to spend. Keep the installed provider route; if included quota is insufficient, stop the pilot rather than silently buying credits or changing providers.

| Pilot | Example model allowance | Metered estimate on currently recorded included treatment |
|---|---|---|
| Source-backed answer | 20 prompts, up to 10k input/1k output each | $0 additional tokens if included; subscription capacity consumed |
| Research and QA | One bounded workflow, up to 20 calls at 30k input/3k output | $0 additional tokens if included; external source retrieval excluded from this fixture |
| Owner workflow/recovery | Deterministic fixtures first; at most 20 interpretation calls at 10k input/1k output | $0 for local deterministic tests; same quota qualification for inference |

Combined allowance: up to 60 calls, 1.0 million input and 100,000 output tokens, before retries/cache accounting. For a separately metered route in a later explicitly authorized comparison, apply its then-verified rates: `1.0 × input dollars per million + 0.1 × output dollars per million`, adjusted for cached tokens and extra tools. No current API price has been substituted for the installed OAuth subscription route.

If all three pilots add 100–400 W above normal load for three hours, the same assumed power rate adds **$0.045–$0.18**. Engineering time, full host recovery, cloud review and paid search are excluded and must be budgeted separately. The cold tests performed here did not run those model workloads.

## Cost verification still needed

Match provider invoices and subscription/credit records to the same UTC window; distinguish manager turns, worker calls, QA/corrections, tools and private review without exporting private contents. Preserve unknown attribution rather than recording zero. Measure idle and active wall power. Compare cost per accepted, evidence-backed outcome, including failed attempts and correction time. No cost-saving claim or migration recommendation follows from this baseline alone.
