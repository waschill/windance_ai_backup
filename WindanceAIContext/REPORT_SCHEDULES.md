# Windance Scheduled Reports

Live schedule reconciled and delivery-tested 2026-09-05. Times are Mountain Time. Verify live scheduler state after future maintenance.

September 22 YouTube update: SAL's loaded Mon–Thu 08:00/12:00/16:00 schedule was
verified and retained. Herald can now update this known schedule through a bounded
adapter with loaded-state readback. Shared creator/section/limit settings are
verified by SAL and Scout. See `projects/HERALD_EXECUTION_RELIABILITY_2026-09-22.md`.
Routine Hermes Telegram restart notices are muted at William's request; this is
separate from report scheduling and task-result delivery.

## Daily delivered reports

| Time | Report | Recipient | Delivery behavior |
|---|---|---|---|
| 6:50 AM | Sentinel router security review | William | Routine all-clear through Telegram; suspicious, blocked, or urgent findings through Max/iMessage |
| 7:00 AM | Network and systems status | William | Routine all-clear through Telegram; attention/outage report through Max/iMessage |
| 7:10 AM | Current-day Training Schedule | Shawn | Daily operational schedule |
| 7:20 AM | Combined daily briefing | William | Telegram; includes deterministic numbered email review |
| 7:35 AM | Prior-day Training Completion Check | William | Telegram; sends only when suspicious rapid completions exist |
| 7:45 AM | Prior-day attendance IP exceptions | William | Telegram; sends only when an exception exists |
| 7:50 AM | Shawn email review and management report | Shawn | Numbered unread inbox review; sender-bound YES/NO approval for changes |
| 8:10 AM | Ledger unpaid-invoice report | Shawn | Daily Odoo operational report |
| 9:00 AM | Morning news briefing | William | Telegram; Frontier AI and social-media marketing |
| 12:10 PM | Read-only email review | William | Telegram; daily midday inbox review |
| 12:30 PM | Shawn email review and management report | Shawn | Numbered unread inbox review; changes require Shawn's approval |
| 5:00 PM | Read-only email review | William | Telegram; daily end-of-day inbox review |
| 5:10 PM | Shawn email review and management report | Shawn | Numbered unread inbox review; changes require Shawn's approval |
| 7:00 PM | Capture Inbox reminder | William | Telegram; sends only when active captures await review |

William's 7:20 AM combined briefing and 12:10/5:00 PM numbered Gmail reports use deterministic Harness report endpoints and SAL's Telegram bridge. Shawn's Training Schedule, email reviews, unpaid-invoice report, and conditional veterinary report remain on iMessage because Shawn does not use Telegram.

William and Shawn can use case-insensitive `ALD` as the short form of `Always Delete` and `NOD` as the short form of `Notify Delete`; the full phrases remain supported. Shawn's changes still require her sender-bound `YES` confirmation. William's existing approval policy remains unchanged.

## Monday through Thursday

| Time | Report | Recipient |
|---|---|---|
| 8:00 AM | YouTube watch briefing (12-hour window) | William through Telegram |
| 12:00 PM | YouTube watch briefing (4-hour window) | William through Telegram |
| 4:00 PM | YouTube watch briefing (4-hour window) | William through Telegram |

## Weekly reports

The YouTube reports permanently exclude Julian Goldie, including his SEO, AI and
Agency channel-name variants, as of 2026-09-22. Enforcement is in SAL's scheduled
generator and Scout's AI watchlist collector; see
`projects/YOUTUBE_CREATOR_EXCLUSION_2026-09-22.md` for verification and limits.

| Time | Report | Recipient / destination |
|---|---|---|
| Tuesday 10:30 AM | Weekly Windance software and AI-stack review | SAL schedules exact-ID local Hermes profile work; Telegram receives only each feature, concise named-agent arguments, and team consensus after Athena's QA gate |

The SAL LaunchAgent `com.windance.weekly-stack-review` owns this recurring local-first review as of 2026-09-03. It gathers structured official release evidence, creates durable staff rows, and invokes Herald's isolated Hermes profiles only by exact task ID; it cannot sweep the legacy pending queue. Codex is a fallback, not the scheduler or default reviewer. William requested the special review immediately on 2026-09-03; the manual production run completed its staff and Athena gates and Max accepted the two-part iMessage with `ok: true`. The unused 2026-09-04 one-shot was then unloaded and moved to SAL's recoverable Trash to prevent duplicate delivery. Delivery validation now examines structured sender fields rather than report prose.

## Conditional business report processing

| Time | Process | Recipient |
|---|---|---|
| 12:20 PM daily | Fall River veterinary report processor | Sends the configured veterinary email only for a pending visit/report, then confirms to Shawn |

## Internal scheduled records—not routine messages

| Time | Process | Behavior |
|---|---|---|
| 9:00 PM daily | Training memory snapshot | Saves Herald's final current-day training snapshot; no routine user message |
| 9:30 PM daily | Herald daily reflection | Saves internal durable reflection; no routine user message |

## Retired during 2026-09-02 reconciliation

- The expired 2026-08-11 I-84 Rocky Canyon one-shot was unloaded and moved to Herald's recoverable Trash archive.
- The orphaned 2026-07-20 Vega trust one-shot files were moved to SAL's recoverable Trash archive; the job was already unloaded.

## Spacing policy

Morning reports that share Herald, Node-RED, or SAL Messages are staggered by at least ten minutes where practical. Noon YouTube, William email, conditional veterinary processing, and Shawn email run at 12:00, 12:10, 12:20, and 12:30. Different-recipient jobs are still staggered when they share the same content or messaging infrastructure.


## Idea Board digest — added 2026-09-19

Friday 4 PM America/Denver: Codex thread heartbeat `weekly-idea-board-and-decision-follow-through`, active and created with an app receipt. Captures are saved immediately to Herald; the digest assesses ideas, recommends up to three next steps and imports new decision logs into canonical Git/indexed context. Results return to the originating Codex thread, not Telegram. Existing 7 PM capture reminder is unchanged. First scheduled digest: 2026-09-25. A future heartbeat run has not yet occurred.
