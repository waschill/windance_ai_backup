# Relationship continuity v1 restore point
Prepared 2026-09-08 on Herald before deployment, all 16 existing profiles.
Protected host-only restore data: /Users/herald/.hermes/backups/relationship-continuity-v1-20260908
Jim's restore files are inside /Users/herald/.hermes/profiles/jim/backups/relationship-continuity-v1-20260908.
No private memory contents, transcripts, raw config, or credentials copied to Git.
Restore selected memory/platform_toolsets config sections from config-sections.json, preserving all unrelated config keys. Restore SOUL.md and USER.md from the matching host-only profile folder only after checking for newer user edits; absent USER.md before rollout is recorded in manifest.json. Do not overwrite later learning blindly.
Implementation uses upstream native memory; no upstream code patch, scheduler, or paid model call.
