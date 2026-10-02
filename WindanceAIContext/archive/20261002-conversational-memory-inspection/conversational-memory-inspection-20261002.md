# Owner-scoped conversational memory inspection — staged

October 2 UTC / October 1 Mountain 2026. Production unchanged; Phase1 open.

The deterministic authenticated memory processor now recognizes `What do you remember about me?`, `show my personal memories`, and `show my business memories` (also list, optional please/Vega address). Unqualified inspection defaults to personal. It obtains the asking owner from the attested source, not a name in the request text. The result shows current source-verified statements with record IDs, revisions and retained-source references so the owner can inspect and correct them. It labels statements as not independently verified facts and discloses retained source messages and earlier answers.

SQL restricts owner, scope, kind and deletion before scanning. Each displayed fact is then verified against its current source hash; absent/changed-source facts are withheld. No sharing grant is interpreted as permission to read someone else's private source, and there is no legacy-store fallback. Implementation bounds each request to50 candidate sources and10 displayed items with500-character quoted excerpts; if more records remain it provides a stable-key continuation command. Those pagination/excerpt bounds are implemented, but large-volume continuation behavior has not yet received a dedicated acceptance test.

## Verified scope

Extended full candidate manager HTTP test invokes its actual message processor with the model bridge forbidden and all sender calls intercepted. Synthetic William personal, William business and Shawn personal memories are created through authenticated intake. William's personal question shows only his personal current fact, excluding Shawn, business and the earlier forgotten fact. Explicit business inspection excludes personal content. Modifying the retained personal source causes the next inspection to withhold that fact. Sender-owner assertions remain correct. Earlier learn/correct/forget, stale-revision, replay, source-redaction and configuration cases continue to pass. No background loop or production database is used.

This verifies the explicit inspection commands, not automatic context injection into arbitrary worker answers, natural-language target disambiguation, inferred habits, source-sharing policy or legacy/mirror containment. Other phrases may still enter the general conversation route. Those remain gates before presenting the system as a fully private adaptive assistant. Current stored source and prior inspection answers are retained even after forgetting a current fact; this is explicitly disclosed and is not complete historical erasure.

## Evidence and recovery

Private test/candidate location: `/Users/herald/services/source-memory-http-20261002`. Reproduce with `test_full_manager_authenticated.py` under the existing Harness Python. The full-source candidate remains private and unchanged from the last builder output; its updated imported processor is included in this archive with dependencies and tests. No production source, schema, credential, service, cursor or route changed, so no production rollback is needed. Use archive hashes to identify this imported-module revision rather than relying solely on the full-source candidate hash.

Next verify the composed memory route across actual process interruption/cold recovery and complete legacy boundary/general retrieval integration, then protected transport provisioning and fresh live rollout gates. No sends, task dispatches, model calls, Odoo writes or new charges occurred. Codex work cost unknown. SAM, SyncThing, Warden suspension, disabled Level8 and disabled phone preserved. Node-RED remains separately blocked.
