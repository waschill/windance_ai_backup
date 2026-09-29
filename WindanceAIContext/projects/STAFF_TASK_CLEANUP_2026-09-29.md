# Staff task cleanup — September 29, 2026

William explicitly requested deletion of all non-pending tasks, then clarified before execution that only future scheduled staff jobs should remain: delete today's assignments and overdue tasks too. This superseded preserving the 17 historical pending rows.

## Applied and verified

At 20:41 UTC, removed 246 Agent Harness staff_tasks and 282 Hermes default Kanban tasks. Included overdue pending rows from July 23 through September 11, completed/archived/failed/blocked/partial/cancelled history, and today's incomplete assignments. Both ledgers had no running work when transaction locks were obtained. Removed associated task notes, delivery/run/revision records, Kanban relationships/comments/events/attachment metadata/subscriptions, and Harness task-search copies. The live staff API and Kanban database subsequently returned zero tasks. Database quick checks passed and Harness health remained ok.

Removed two disabled August 27 parcel-tracking cron jobs with stale next-run timestamps through Hermes' existing remove_job function. No active native Hermes cron jobs remained. Existing recurring LaunchAgent schedules, Node-RED schedules and Codex automations were not changed. HERALD and SAL calendar plist hashes matched before and after. Warden was paused for cleanup, then resumed; fresh status showed unpaused with all configured checks passing. No scheduled job was replayed.

## Context for future staff conversations

The AI product-ideas assignment had never reached the staff correctly. Forge task 2efec55b contained only the follow-up instruction to correct the request and begin, omitting the original assignment, and blocked immediately. Reacher later cited it as pending/started despite that status. No matching concepts, prior-art checks or durable concept memory receipts were found. The failed task is now deleted. William plans to resubmit; do not claim that the earlier assignment is active or completed. This cleanup does not repair the conversational handoff defect or create a replacement assignment.

Historical project documents may cite deleted task IDs. Their old verification claims remain historical; those task endpoints no longer resolve. Shared memories, conversation history, decision logs, reports, workspaces and original Kanban attachment files remain. Future scheduled runs may create new task records normally.

## Private recovery

HERALD: /Users/herald/services/task-cleanup-backups/20260929T204132Z

Contains verified task-only JSON exports, obsolete cron job definitions/output backups, and receipt.json. Task export SHA256 values: staff 5f7a643d41c9ff4f9097f89712ea3f079573afffc35589aced337048a76b4eb5; Kanban 62ddba1b777397a2ac423b11f4bbce64fdbfb25d900390eb65febd4859f903cd. Private contents must not be published. Recovery must be selective and reviewed against newer state; never replace whole live databases or replay old jobs merely to restore history.

No service code, model routing, business records, SyncThing, or Level 8 configuration changed. The unrelated global Claude review suspension remained active; this was William-directed ledger cleanup, not a Warden-proposed autonomous repair.