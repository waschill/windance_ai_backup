# Reacher telephone conversation adjustment — September 29, 2026

William confirmed that a real inbound phone conversation now works after the runtime repair. He then reported two repetitive behaviors: the identical acknowledgment before every utterance and the name Reacher spoken before each answer.

The first was literal connector code in begin_turn, not a model improvisation. The second came from the shared identity instruction to label written replies as Reacher. The phone connector no longer injects the stock acknowledgment. The phone-only model instructions now say the connector has already introduced the assistant once, answer naturally without speaker labels or repeated greetings, and identify himself if explicitly asked. Shared identity files and other channels are unchanged. Truthful tool receipts, access boundaries, the one initial greeting, runtime bootstrap and startup-failure cleanup remain intact.

Verification: 21 phone tests pass. The revised first-response assertion fails against the old code with the exact unwanted sentence and passes with the correction. A fresh actual-worker protocol conversation returned two natural responses without the name prefix or stock acknowledgment, then handled goodbye and cleanup. The synthetic prompts were harmless conversation and arithmetic; no business action or outbound call was requested. Prior physical call confirmation applies to the runtime correction, while physical listening of this separate style revision remains pending.

Private evidence is under /Users/herald/services/herald-phone/repair-20260929/conversation. Deployed at 15:59:41 UTC (09:59 Mountain), after an explicit idle health check. Only phone_service.py, worker.py and test_phone_service.py were replaced, with both prior-source and reviewed-candidate hash guards. The dedicated phone job was stopped, its PID was confirmed gone, and then it was bootstrapped again. Origin and public health returned configured=true, active_call=false. The installed-source actual-worker style canary passed after deployment in 13.25 seconds, with readiness at 4.04 seconds, two unlabelled responses, goodbye and call-slot cleanup. Main owns Warden maintenance and resume for the combined repair.

Private Claude APPROVED the exact revision: session `20260929_095616_249fb1`, verdict SHA-256 `24c1fcb9490a3f13bf98187118f24782ee51660be8efeb097121d87b3be507c0`, packet manifest SHA-256 `6ae9beb508fdb3898bb4fb5893fc6c463313e24c74c180cbe0018472e3dca0ea`. The review accepted pre-existing harmless leading whitespace and noted that unchanged durable-task authorization clauses were not re-exercised by the style-only canary.

Current SHA-256 values:
- phone_service.py: `cbdb0cf7f2d17161f2f7dda33a1a97907280dd4f5818ceffe829ade8d3e93141`
- worker.py: `85f013575d748797418b4eeeee559137b520772f237e7ee9d01c81e0f9b67d2c`
- test_phone_service.py: `9ea54ceb24c35b81a9d3b6ab39d4a951cf07cd8c70aa1b3821ce241014fe3bc5`

Backup: `/Users/herald/services/herald-phone/backups/20260929-before-conversation/`. Restore only those three files while idle and restart the dedicated phone job to undo the conversation adjustment; this backup retains the preceding runtime and failure-release fixes. Private evidence includes tests.txt, ack-red.txt, installed-style-relay.json, deployed.json, claude-receipt.json and claude-verdict.txt. No outbound call was placed, and neither shared identity files nor any other channel was changed. Physical listening of this style revision remains unverified; William's confirmed working call preceded it.

## Superseded route — later September 29
William subsequently requested the phone be routed to Vega. The manager-backed worker and greeting are now installed; shared carrier/access/voice settings remain. The earlier source hashes above are historical, not current. See VEGA_MANAGER_2026-09-29.md for current verification, limitations and recovery.

