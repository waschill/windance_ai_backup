# Windance Software Maintenance Policy

## Governing rule

Operational capabilities are paramount. Upgrade managed software without requesting approval when the release preserves Windance operating procedures and capabilities. Before any upgrade that would fundamentally change an SOP, workflow, authorization boundary, routing architecture, data meaning, or required human procedure, report the proposed SOP impact to William and obtain his approval.

Semantic version numbers alone do not decide approval. Release notes and implementation impact do.

## Mandatory sequence

1. Inventory installed and available versions across HAL, Herald, SAL, AL, SAM, managed containers, models, package managers, and Windance applications.
2. Classify SOP impact using release notes and local implementation analysis.
3. Stop and ask William only when a fundamental SOP change is identified.
4. Create a sanitized, dated restore point in the private `windance_ai_backup` GitHub repository.
5. Confirm the pushed GitHub commit. Never force-push, rewrite, prune, or delete backup history.
6. Upgrade routine/approved software.
7. Record results and observable health. A failed check or blocked upgrade is an explicit failure, never “current.”

## SyncThing

SyncThing software may be upgraded. Its schedules, folder definitions, device configuration, database, bind mounts, synchronized data, and operational behavior must remain unchanged during routine maintenance. Never place SyncThing keys, certificates, credentials, database contents, or synchronized user data in GitHub. Verify configuration/data bindings remain identical across a container or package upgrade.

## Approval-required examples

- Replacing a working workflow or front door.
- Changing who may approve or execute consequential actions.
- Breaking data/schema migrations or changed business semantics.
- A major OS/platform migration that changes operating procedures.
- Moving services between nodes or changing production routing.

Routine patches, security updates, compatible dependency updates, browsers, models, and application releases proceed automatically when the above conditions are not present.
