# Task continuity restore point — 2026-09-09

Pre-change full code backups remain on Herald under /Users/herald/services/task-continuity-backup-20260909. A SQLite online backup of the Harness database is kept there only; it contains private operational history and is excluded from Git. This archive stores sanitized code excerpts and source hashes. No raw configs, credentials, private memories or database content are published.

Restore only the affected source files after checking for newer edits; restart com.windance.agent-harness if restoring Harness code. Do not replace the live database with an old snapshot unless recovering corruption and explicitly accepting later data loss. The additive task-note table can remain inert on code rollback. Preserve new task records and notes. The profile runner remains exact-task-only.
