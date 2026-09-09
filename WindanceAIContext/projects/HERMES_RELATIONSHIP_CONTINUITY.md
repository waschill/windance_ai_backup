# Hermes relationship continuity — installed 2026-09-08

William requested assistants that develop familiarity through remembered preferences and feedback while retaining individual personalities. This implementation uses Hermes 0.21.1's existing profile-local memory and identity loading, not model retraining or a new memory service.

## Everyday use

Talk naturally. Each bot is instructed to selectively retain clear, lasting conversational preferences and corrections. For certainty, say:

- “Remember that I prefer a short answer first, with details available if I ask.”
- “That was a joke; remember that I enjoy this kind of banter, not the fictional claim.”
- “I've changed my mind about that preference. Replace it with this one.”
- “What have you saved about how I like to work with you?”
- “Forget that preference.”

A bot may say a write awaits approval. That is a pending candidate, not saved memory. Root/default Hermes retains its pre-existing memory write-approval requirement; the 15 named profiles retain their previous ungated memory-write setting. No approval gate was disabled. Forgetting removes active memory, not past chat transcripts or protected rollback files.

## What is installed

All 16 profiles: default (Hermes), Herald, Sentinel, Tactical, Kanak, Archivist, Athena, Forge, Iris, Jean, Jim, Ledger, Max, Sandbox, Scout, and Vega.

- A marked Relationship continuity section in each SOUL.md preserves the existing persona and adds selective remembering, correction, forgetting, conversational warmth, uncertainty, privacy, and truthful save receipts.
- Each profile's memories/USER.md contains a separately stored, dated seed of William's directly stated name, warmth/humor, individual-voice, privacy, and cost preferences. No chat transcript was harvested. Existing entries were preserved.
- Native memory and user-profile loading are enabled. Native memory tools were added to explicit configured channel lists where absent. Root's composite lists remain intact. No operational tools were added.
- Memory capacity is at least 4,000 characters for agent notes and 2,400 for user preferences, retaining any larger existing limits. Actual loaded content determines token use; empty capacity costs nothing.
- Jim has only memory in his effective configured toolset. An implicit Kanban recovery was suppressed using agent.disabled_toolsets, and the old blanket “no tool merely to remember” wording now allows only the real private memory tool. His existing confidentiality instructions remain. His rollback memory is also inside his own profile.
- Kanak's old “Never pretend to be unintelligent” phrase was changed to “Keep your intelligence evident.” Hermes's scanner had matched the negated phrase and rejected his entire SOUL.md. All 16 identity blocks now load through the actual native scanner.

## Privacy, cost, and limits

There is no shared writable relationship memory, cross-profile transcript harvest, new external provider, new scheduler, or recurring reflection/model job. Existing external-provider configuration is preserved. Added instructions and remembered facts consume some context tokens in ordinary conversations, and a memory-tool write may require an additional normal model continuation. No paid model calls were made for deployment or verification.

Isolation is Hermes profile scoping plus explicit privacy instructions, not a new OS sandbox: operational bots already capable of filesystem access still run under Herald's account. This rollout grants no new such access. It must never be advertised as an impermeable security boundary.

Model judgment still determines whether a preference is recognized and a memory tool is used. Passing infrastructure tests does not prove every model will remember perfectly. Watch actual save receipts and fresh-session behavior. The policy requires sensitive details to be saved only on a specific request, and excludes credentials, jokes-as-facts, inferred diagnoses, and changes of operational authority.

Fresh agent sessions load the new tool configuration and memory snapshot. Existing live sessions may retain their old tool surface or snapshot; new group threads may reuse the room's member sessions. No service was restarted during this rollout and no ongoing conversation was interrupted. For immediate adoption in an existing room, arrange an idle dashboard restart or fresh member sessions; do not delete history as a refresh mechanism.

## Verification and maintenance

Durable code: /Users/herald/services/windance-relationship-continuity

Run with /Users/herald/.hermes/hermes-agent/venv/bin/python:

1. deploy-relationship.py verify — real native config/toolset resolution, memory loading, identity loading, profile path checks, approval preservation, and no unrelated capability additions/losses, for all 16 profiles.
2. test-relationship-memory.py — disposable native memory-tool tests: save, recall in a fresh process, isolation, correction, forgetting, capacity rejection, and approval staging. No model calls or production memory mutations.

All tests passed on 2026-09-08. Dashboard status remained healthy, authenticated, version 0.21.1. Pre-existing unused root Teams/Google Chat composite-name warnings were observed while comparing tool resolution; their configuration was left intact.

New bots do not acquire this policy automatically: review their persona/privacy rules and provision their own native memory and marked policy deliberately. The deploy script's prepare/apply steps intentionally refuse repeat deployment; verify is safe to rerun. Future Hermes upgrades should run verification; these files are outside the upstream checkout.

## Restore

Pre-change checkpoint: Git 30b3701, with protected host-only profile backups under /Users/herald/.hermes/backups/relationship-continuity-v1-20260908. Jim's backup is /Users/herald/.hermes/profiles/jim/backups/relationship-continuity-v1-20260908. Private memories and raw configs were not copied to Git or context mirrors.

Restore only the selected memory and platform_toolsets configuration sections from each config-sections.json, preserving all unrelated keys and credentials. For Jim, also restore agent.disabled_toolsets from agent_disabled_toolsets. Restore that profile's SOUL.md and USER.md only after reviewing newer edits/learning. The manifest records files absent before rollout. Never blindly overwrite later memories. No MEMORY.md content was changed by this deployment.
