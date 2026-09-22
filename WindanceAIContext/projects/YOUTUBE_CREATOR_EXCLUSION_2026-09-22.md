# Permanent Julian Goldie exclusion — 2026-09-22

Status: APPLIED AND VERIFIED on SAL and HERALD.

William permanently excludes Julian Goldie from suggested YouTube videos. This
includes the SEO, AI and Agency channel-name variants. He should not need to
repeat the preference when requesting another report.

## Incident and cause

At 09:14 Mountain on September 22, Herald acknowledged William's request to
exclude Julian Goldie from the video suggestion task and claimed to have updated
future operational constraints. At noon SAL's scheduled AI / YouTube Watch still
included `New FREE Hermes Agent Model!` by Julian Goldie SEO (dT7eAa2TeAU).
The morning report also contained a Goldie video, before that acknowledgment.

Live inspection found no exclusion in SAL's actual scheduled generator,
`/Users/zuzu/bin/windance_youtube_briefing.py`. Broad YouTube searches could
therefore return his videos even though he was not a named feed seed. Herald's
claim did not establish or verify a change to this producer. Separately, Scout's
metadata collector only excluded Goldie when that word appeared in the current
task request; the September 17 watchlist repair had not made it permanent.

## Applied changes

- SAL filters creator names in search results before the result limit, in the
  shared deduplication/selection path, and in the latest-channel section.
  Matching ignores case, spacing, punctuation and Unicode compatibility forms.
  Unidentified creators are omitted because their exclusion cannot be checked.
- HERALD's `services/profile-staff-runner/watchlist_evidence.py` always applies
  its Goldie search/metadata exclusion for supported AI watchlists.
- `scout_research_policy.py` tells Scout and Athena that the preference is
  permanent even if the current request does not mention it.
- Schedules and delivery routes are unchanged. No replacement report was sent.

## Verification

- Four SAL regression tests passed before deployment and against deployed code:
  channel variants, unknown creators, search limiting, all report sections and
  historical log entries. All 83 retained Goldie report entries were rejected.
- A HERALD collector/contract regression passed before and after deployment:
  a task with no Goldie keyword rejected SEO, AI and Agency variants while
  retaining Matt Wolfe.
- A fresh 12-hour public-source print-only preview returned allowed videos and
  no Goldie entry. No outbound send was invoked.
- Drift checks matched original hashes, originals were backed up, and deployed
  hashes matched the tested candidate files. Agent Harness health remained ok.
- SAL's loaded LaunchAgent points directly at the changed script and last exit
  status was zero. Each scheduled invocation loads the new file; no restart is
  required. Fresh Scout task processes load the updated modules.

## Use, limits and recovery

Use the normal scheduled reports and ordinary Scout AI-watchlist requests.
The next scheduled delivery itself has not yet occurred in this verification.
The SAL check uses reported creator names; an unknown future channel rebrand
that does not identify Goldie would require an additional identity rule.
Scout's deterministic metadata path is scoped to its recognized AI watchlists;
the general watchlist instruction also carries the permanent preference.
This repair does not implement a general conversational preference editor.
Herald must not claim future scheduler changes without an actual producer change
and verification receipt.

Private source/test/deployment packets and original `.before` backups are in
`/Users/zuzu/services/youtube-exclusion-20260922` on SAL and
`/Users/herald/services/youtube-exclusion-20260922` on HERALD. Restore the matching
original files to their production paths to roll back. Local operator working
files are in HAL's `Documents/Codex/2026-09-22/i-am-confused-i-asked-herald`.
Only sanitized operational notes belong in the shared context repository.
