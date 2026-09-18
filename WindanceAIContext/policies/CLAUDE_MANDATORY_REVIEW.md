# Mandatory Claude review before code execution or deployment

Effective 2026-09-17. Standing instruction from William to Vega (Codex).

## Current status — suspended 2026-09-18

William explicitly instructed Vega to bypass all reviews until further notice.
Therefore this mandatory-review requirement is suspended for all work beginning
2026-09-18 and remains suspended until William explicitly reinstates it. Claude
review may still be requested voluntarily when useful, but it is not a gate to
testing, execution, or deployment while this suspension is active. All other
authorization, safety, backup, verification, and documentation requirements
remain in force.

All changes to code, and all stack changes that require code, must be reviewed by Claude before the changed code is executed or deployed, unless William explicitly specifies otherwise for that task. This includes scripts, one-off mutation commands, migrations, automation, infrastructure-as-code, executable configuration, and code Vega commissions, accepts, runs, or deploys through other agents. Delegating execution does not bypass this requirement; Vega must arrange review before the delegate runs changed code. Small size, reversibility, urgency, successful tests, or confidence do not create exemptions.

Vega may inspect existing state and prepare an inert proposed patch and review packet. Obtain Claude's review before running changed code, including tests/canaries that execute it, or applying it to a live stack. A proposal may be prepared in a workspace that does not auto-run or auto-deploy it. Submit the actual proposed diff/files, requirements, relevant context, intended execution/test/deployment commands, and rollback plan through Claude's private review lane. Exclude secrets and unrelated private material.

The review must correspond to the version being executed/deployed. Submit a manifest of review files and SHA-256 hashes, with the file count; ensure all relevant material was actually available and reviewed, splitting files to fit the packet limits when necessary. Record the Claude session ID, manifest/revision, findings, and Vega's disposition. A review covers only the listed, inspected material, not omitted or truncated files. If code or the material execution/deployment plan changes after review, submit the changed material for review before running it. After authorized execution, record actual test results and seek follow-up review when results require changes or reveal unresolved concerns. A proposal, queued request, or timed-out/incomplete response is not a completed review.

Claude is advisory and reports to Vega. Vega evaluates the findings and retains final implementation/deployment judgment under William, recording reasons when disagreeing. Disclose any decision to proceed despite a high-severity finding to William. Mandatory review does not mean Claude replaces Vega as decision maker. Other safety boundaries and required authorizations still apply.

Only William can exempt a task from review or require review of a disputed case. If Vega believes review is unnecessary, ask William with the exact task, scope, and reason; wait for his decision before the covered execution/deployment. Silence, elapsed time, general permission to proceed, full access, or another agent's approval is not an exemption. Record William's explicit exception and apply it only within its stated scope; do not turn it into a standing exemption. When scope is uncertain, obtain review or ask William rather than self-exempting.

If Claude is unavailable or the review cannot be completed, stop the covered execution/deployment, explain the blocker, and ask William whether to wait or grant an explicit exception. Do not substitute self-review or another model without his direction.

## Private review access

On HERALD, put sanitized material under `/Users/herald/services/claude-review/packets` and use the existing operator wrapper:

`/Users/herald/.hermes/hermes-agent/venv/bin/python /Users/herald/services/claude-review/claude_review.py --query-file PATH [--resume SESSION_ID]`

Claude uses `anthropic/claude-opus-5` through OpenRouter with no fallback and read-only packet tools. Vega directly initiates these reviews; this policy does not give Herald/Forge an automatic Claude assignment route. See `projects/CLAUDE_INDEPENDENT_REVIEWER_2026-09-17.md` for the verified setup.

## Persistence and limits

This policy is installed in Vega's global AGENTS.md on HAL and HERALD and linked from the shared bootstrap. It is a standing agent instruction, not a technical shell/deployment interlock. Existing sessions must follow William's instruction immediately; new sessions discover it through their persistent instructions. Policy changes or exemptions remain William's decision. There is no automatic emergency or rollback exemption. Pure inspection of existing state, such as reading logs or running git status, does not execute changed code. If applicability is disputed, obtain review or ask William.

