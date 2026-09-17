# Scout source-first lookup repair — 2026-09-17

## Problem and deployed behavior

Scout task `422f430b-5536-4c0d-a727-e48b2bbdd68d` stopped after reading general Hermes documentation and reporting a search network error. The official latest release was readily available. Inspection found that the runner applied medical-source requirements to software lookups, used a research-keyword test that missed “look up the latest version,” and expected an Athena verdict format inconsistent with her profile.

The production profile runner now reviews every Scout assignment with Athena. A narrow software-version lookup may use one authoritative publisher release record; broad and high-stakes research retain their stronger evidence requirements. Medical/veterinary domain checks now parse actual URL hostnames instead of accepting domain text embedded in an unrelated URL.

For known Hermes Agent and Ollama software-version requests, the runner first retrieves the official GitHub Latest API record. If that fails, it retrieves the publisher's GitHub `/releases/latest` page directly, verifies the redirect to the exact official release tag, and extracts the title and publication timestamp. The latest-source receipt includes attempted URLs, outcomes, and check time. Search and extraction indexes are not involved in those direct checks. No API credential or new paid provider is needed.

Scout's policy now requires source-first version research, distinguishes latest stable from installed versions and prereleases, permits a successful authoritative fallback after a search failure, and requires available read-only recovery attempts before reporting an unresolved lookup. General documentation and model memory do not establish the current release. Harness assignments explicitly override the generic Kanban instructions.

The completion gate rejects missing versions/citations and mismatches with a successful official release receipt. Athena accepts her existing first-line `Verdict: PASS` format as well as `APPROVED`, while negative or ambiguous verdicts stay rejected. A failed lookup keeps one consistent status and does not concatenate the entire internal QA critique into William's report.

## Verification

- Nineteen regression tests pass, covering version matching, one-source lookup acceptance, missing answers, high-stakes source protection, hostname spoofing, API-to-page fallback, unverified failures, QA verdict parsing, and consistent blocked status.
- Live normal lookup: Scout returned Hermes Agent v0.21.3, released September 14, 2026, tag v2026.9.14; Athena approved.
- Live forced API/search outage: the public release-page fallback recovered the same version and date; Athena approved. Faults were injected only inside isolated canary processes, not production search configuration.
- Live complete retrieval outage: Scout withheld a version instead of inventing one. The final rerun returned one consistent BLOCKED status; Athena did not approve completion.
- Production-ledger canary `4dd83d6a-66ea-43bc-9841-6220da1bbe91` completed with the correct release and Athena approval through the real create, dispatch, start, and completion path. Harness health was `ok`; the internal canary produced zero outbound delivery receipts.
- Earlier canaries caught a `v`-prefix parsing defect and stale extracted release data. Those defects were corrected before final acceptance; direct public release-page retrieval is the recovery path now.

## Components, usage, and limits

Production files:
- `/Users/herald/services/profile-staff-runner/profile_staff_runner.py`
- `/Users/herald/services/profile-staff-runner/scout_research_policy.py`
- `/Users/herald/.hermes/profiles/scout/SOUL.md`

New Scout assignments use the changes automatically. No service restart, new command, paid search provider, or user approval ceremony is required. Existing Hermes chats may retain old profile context; fresh assignments load the updated policy.

The deterministic product registry currently covers Hermes Agent and Ollama software releases. Other products use Scout's source-first tools and Athena review. Direct HTML parsing fails closed if GitHub's markup or metadata becomes ambiguous. If all accessible authoritative paths fail, no latest-version claim is made. This does not grant software-installation, mailbox, outbound messaging, or infrastructure-mutation authority to Scout.

## Evidence and recovery

The sanitized implementation and tests are preserved in `projects/scout-lookup-20260917/`.
Live canary workspace and detailed audit outputs: `/Users/herald/services/scout-lookup-staging-20260917/`.
Pre-change originals: `/Users/herald/services/scout-lookup-staging-20260917/backup/profile_staff_runner.py` and `backup/SOUL.md`.

To roll back, restore those two original files to their production locations when no profile task is active. The new helper module may remain unused. No gateway restart is needed for the runner; verify a fresh bounded task afterward. Do not sweep or replay older pending tasks.

Publish with `scripts/publish-windance-context.ps1 -PushGit`; its final step verifies indexing. Also query `SCOUT_SOURCE_FIRST_LOOKUP_2026-09-17` to verify retrieval of this specific repair record.

