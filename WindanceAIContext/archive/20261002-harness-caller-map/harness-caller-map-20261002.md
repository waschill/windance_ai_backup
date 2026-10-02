# Harness caller compatibility inventory

Source candidates and direct LaunchAgent registrations inspected on HERALD/SAL. This is a scoped migration input, not a complete live dependency map or permission deployment.

24 HERALD top-level Python source candidates and four SAL bin Python candidates contain Harness address/base markers. Initial broad recursive search mixed historical staging copies with current files; it was discarded in favor of the attached bounded scanner. The final scanner excludes dated/staging roots and known historical filename forms, records hashes and literal endpoint paths, and correlates exact ProgramArguments script paths with both current user/gui launchd domains. No source credential values, plist environments, contacts or message bodies are exported. Header mentions are lexical evidence only, not proof of effective authorization.

| Caller | Observed role | Required compatibility treatment |
|---|---|---|
| SAL imessage_herald_bridge.py | Registered/running gui job; /message; sender-to-owner mapping previously inspected | Preserve sender-derived owner, stable source row and reply route; authenticate adapter; verify direct-chat provenance before private context |
| HERALD vega-manager/manager.py | Registered/running user job; message intake and staff calls | Preserve immutable ingress identity through durable messages and worker tools; no missing-owner default for private memory |
| HERALD staff_follow_through_monitor.py | Registered/running user job; /staff/follow-through | Service-only maintenance identity; no person-private-memory grant by default |
| daily_training_schedule.py | Source references /training/today and /memory, kind daily_training_schedule | Business source; preserve report behavior and use explicit producer scope; registration not established by direct-path scan |
| desktop_context_sync.py | /memory, kind desktop_context, global latest key; saved job unregistered in checked domains | Do not resume or classify as business automatically; source content/privacy and replacement ownership need review |
| daily_reflection.py | /reflection/daily; saved job unregistered in checked domains | Reflection combines context; owner/scope and source selection need explicit reconciliation before resumption |
| SAL windance_weekly_stack_review.py | Registered scheduled gui job, currently not running; /memory and staff routes | Business review provenance; separate schedule owner from conversational owner; do not duplicate existing release watch |
| gmail sender sweep, urgent monitor, software maintenance | Saved direct-path definitions not registered in checked domains | Investigate current ownership/replacements before recovery; no automatic reinstatement |

Nightly core maintenance and weekly stack maintenance are registered scheduled gui jobs, currently not running. Scheduled idle is not service failure. The scan separately confirms manager and staff-monitor registrations survived this observation interval; it does not establish reboot persistence.

Unverified coverage: Node-RED flows (access hold remains), SAM application caller source, HAL services, Hermes dynamic/plugin-loaded adapters, non-Python callers, shell wrappers, system LaunchDaemons, env-composed URLs, and actual request traffic. No assumption that an unmatched file is active or inactive. Route literal extraction is incomplete for dynamic URL assembly. The source memory metadata inspected for training and desktop writers has no explicit person/scope field; nonempty source strings alone cannot grant access.

Rollout must preserve read-only business/report routes and SAM availability while adding scoped memory operations. Do not globally replace shared credentials or require new credentials on every existing route until each active caller is reconciled. Existing unclassified facts remain preserved, not assigned guessed owners. First integrate an authenticated sender path end to end in isolation, then verify current backups, deployment/rollback, and natural report compatibility. No services restarted, credentials changed, reports sent, Odoo calls or production memory writes. Zero model calls. Phase 1 remains open.

Evidence: inventory_harness_callers.py, herald-caller-inventory-20261002.json, sal-caller-inventory-20261002.json. No recovery action needed for this read-only inventory.
