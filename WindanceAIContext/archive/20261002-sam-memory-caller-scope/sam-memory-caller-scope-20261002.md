# SAM legacy-memory dependency and required caller scope

October 2 UTC / October 1 Mountain 2026. Read-only source/service inspection; no SAM interruption or API operation.

The installed sam-schedule.service is loaded, active and running, and its ExecStart matches `/home/williamschilling/services/sam-schedule/sam_schedule.py`. SHA824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1. In that source, commit_day at line1743 contains the /memory endpoint and writes kind `sam_daily_schedule`, key `date_key`, a rendered schedule/totals value, confidence0.92 and source label `SAM schedule display`. This establishes a dependency in the running application's source, not proof that a recent commit succeeded or that notes collection is active.

sam-schedule-nightly.timer and sam-schedule-refresh.timer are loaded, active/waiting. Their corresponding oneshot services are loaded/inactive, which is consistent with scheduled idle; it is not a failure or evidence of successful recent execution. Exact direct source-path matching did not resolve their wrapper commands, so wrapper provenance and recent outcomes remain unverified. No timer was triggered, restarted or edited.

Two other top-level source files also contain older schedule/memory paths. The running main-service path matched neither. Treat their activity as unverified, not automatically retired. Full metadata and hashes are in the scanner receipt. The scan reads source syntax and named unit properties only: no application import, schedule/history database, private record, /memory request, Odoo call or Node-RED access.

## Concrete compatibility requirements

Do not blanket-disable legacy POST /memory before replacing this dependency. The proposed SAM service credential must identify SAM as a producer, not claim William or Shawn as a human. Its permitted write contract should be limited to the verified daily-schedule kind, canonical validated date key, bounded expected payload and server-owned source label. It must not inherit private memory reads, arbitrary kind/key writes, graph access, staff dispatch or mailbox permissions. Actual credential/transport provisioning and write compatibility are not installed or proven by this report.

Preserve existing successful/retry semantics after inspecting commit_day response handling and its timer wrappers. New canonical business-source storage needs producer provenance and explicit reader policy; do not silently migrate shared historical values into an assumed personal owner. Existing root Training/Odoo restrictions remain unchanged. Shawn's detailed training-note collection remains suspended; this dependency observation does not authorize re-enabling it or treat its deferred pilot as a blocker.

HERALD training/desktop/reflection and SAL weekly-review candidates remain documented in the earlier bounded caller inventory; their registration status was not refreshed by this SAM-only scan. Node-RED caller coverage remains access-blocked. Other shell/dynamic/plugin callers still need reconciliation. Therefore this is one verified live dependency, not a complete allowlist or authorization to change the global Harness credential.

## Evidence and recovery

Archived scanner `inventory_sam_memory_dependencies.py` and sanitized `sam-memory-dependencies-20261002.json` record source hashes, literal paths/kinds and unit state. Temporary script copied to `/tmp/windance_inventory_sam_memory_20261002.py`; it makes no configuration mutation and requires no production rollback. The selected dictionary shape was inspected without runtime values or credentials. Zero model calls, sends, task dispatches, database reads, API calls or paid commitments. Codex cost unknown. SAM protected hours22:00–05:00Mountain remain in force; no interruption occurred. Warden suspension, SyncThing, disabled Level8 and phone preserved. Phase1 open.
