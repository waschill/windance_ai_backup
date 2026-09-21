# SAM Schedule Display

SAM is the Raspberry Pi 5 barn schedule node.

## What it does

- Hosts a portrait-friendly web schedule at port `8088`.
- Pulls daily schedule data from Herald/Odoo.
- Pulls Farrier/Vet flags from the Odoo Horses model.
- Stores touch completion state locally in SQLite.
- Lets Training, Farrier, and Vet cells be completed independently.
- Requires confirmation before undoing a completed cell.
- Commits the completed day back to Archivist memory on Herald.
- For supported Training cells, completion opens a category/subcategory, short-note,
  and one-to-five-star form. Saving the form records the detail and completes the
  cell atomically; cancelling leaves the cell incomplete. The form prefills from
  that horse's most recent record for the same training type.
- Automatically updates once after 5:00 AM.
- Automatically commits at/after 11:55 PM if the day has not already been committed.

## URLs

- Schedule (Wi-Fi): `http://192.168.36.29:8088/`
- Admin: `http://192.168.36.29:8088/admin`
- Health/status: `http://192.168.36.29:8088/api/status`
- SAM is Wi-Fi-only; the former `192.168.36.230` wired route is inactive.
- The Time Clock button opens the Odoo Attendance kiosk directly as of 2026-09-11. The legacy `wdftime.com` frame is bypassed because its BizLand host serves a certificate for `*.bizland.com`, not `wdftime.com`.

## Training code parser

- First letter is trainer except standalone `F`.
- `S` = Shawn
- `K` = Skye
- `W` = William
- `L` = Lynda
- `T` = Teaghan
- `F` = Freewalk
- `R` = Ride
- `G` = Ground Work
- `D` = Drive
- `Bit` = Bit
- `L` = Lunge

Example: `KLBit` = Skye: Lunge + Bit.

## Training completion detail

Production deployment was verified on 2026-09-05. Supported type prefixes are
`R` (Riding), `D` or `T` (Driving), and `G` or `L` (Ground Work). Schedule cells
containing a time use the generic Lesson form. Freewalk and unmapped codes keep
the original one-tap completion behavior. As of 2026-09-06, rows whose displayed
name begins with `Feed` are also exempt from the popup and retain one-tap
completion. Detail records are stored locally in
SAM SQLite table `training_completion_details` and are exposed with committed
history through `/api/history`; this feature does not post to Odoo or decrement
Odoo lesson bundles.

### Popup suspended — 2026-09-20

At William's request, the category/subcategory, stars, and notes popup is
suspended. New Training taps use SAM's ordinary one-tap `/api/cell` path and
record only the scheduled code, horse/display row, trainer, and completion
timestamp. The detailed submission endpoint returns HTTP 410, so a stale or
external client cannot add new ratings or notes. Existing historical detail
records remain preserved and readable; none were deleted. The live SAM service
and kiosk browser were restarted, the page was verified to contain the disabled
popup branch, and health remained `ok`. Rollback source:
`/home/williamschilling/services/sam-schedule/backups/sam_schedule.py.before-popup-suspension-20260920-2330`.

## Vet completion audit — 2026-09-05

Read-only inspection found that the 2026-08-04 Vet commit successfully created
five Odoo Veterinarian history records, but SAM has no need-clear receipts for
that visit. The need-clearing code was deployed afterward, and `commit_day()`
returns immediately for an already committed day, so that historical commit was
never revisited by the newer clearing step. The current implementation also
clears only `x_studio_needs_vet`; it does not clear `x_studio_vet_needs`, because
the Herald guarded Odoo writer currently permits only the Farrier/Vet boolean
fields. Live read-only comparison confirmed that some August notes or flags were
later changed in Odoo. No Odoo record, SAM record, or clearing policy was changed
during this audit.

## Deployment target

`/home/williamschilling/services/sam-schedule`

systemd service:

`/etc/systemd/system/windance-sam-schedule.service`

## Odoo lesson-package foundation

As of 2026-08-29, the production Odoo Studio `Lesson Tracker` app has a
`Lesson Bundles` menu backed by custom model `x_lesons`. The bundle form now
includes Student, Package Product, Source Invoice, Source Invoice Line, Sales
Order, Lessons Purchased, Lessons Used, and Lessons Remaining. The existing
service products `Lessons 10-Pack` and `Lessons 4 Pack` are configured with
`Creates Lesson Tracker` enabled and 10 / 4 lessons included respectively.

Odoo automation `Create Lesson Bundle when Invoice Enters In Payment` is
active on customer invoices. It watches Payment Status and invoice Type, then
creates one bundle for each qualifying lesson-package invoice line when the
invoice enters `In Payment`. The action links the exact invoice line and checks
for that link before creation, making retries duplicate-safe. Historical
invoices were not backfilled because prior lesson usage must be reconciled
before assigning opening balances.

The bundle form exposes its existing one-to-many child table as the future
Lesson Usage ledger. The next implementation phase is to add SAM event fields
to that child model and create the narrowly guarded Herald/SAM posting route;
SAM does not yet decrement Odoo lesson balances.

## Requested reboot — 2026-09-08

Rebooted SAM through the configured SAM-WIFI SSH alias at William's request.
Verified a changed Linux boot ID, restored SSH access, active sam-schedule and
LightDM services, HTTP 200 from the schedule homepage, and Chromium running
with the schedule kiosk URL. No failed systemd units were reported. The older
documented /api/status URL returned 404; the homepage was used for this check.

## Farrier/Vet date-gating source repair — 2026-09-18

Odoo automation 1983 (`Populate Horses`) was incorrectly appending current
Farrier/Vet need text into ordinary weekday Training fields whenever a service
visit fell in that week. It never removed those copied phrases when the visit
date changed. The automation now only ensures Training-status horses have
worksheet rows; it no longer reads, writes, or cleans service notes in Training
fields. SAM remains the sole display path for service needs: it reads every
horse directly and shows Farrier/Vet text only when today's date exactly equals
the corresponding Work Schedule visit date.

Fourteen confirmed Farrier phrases were removed from the active Friday Training
cells while preserving legitimate codes (`F`, `RS`, `DW`, `FBit`). Every removed
phrase matched the horse's current Farrier need. Horse need flags and note text
were not changed. Six older matching rows are orphaned from every Work Schedule
and cannot display, so they were deliberately left untouched. After refresh,
SAM reported Farrier due false, Vet due false, empty service columns, and no
copied service phrases in active Training cells. Next dates remained Farrier
2026-09-22 and Vet 2026-10-26. Backup:
`/Users/herald/backups/odoo-service-date-gate/before-20260918-153658.json`.

## Human-only Odoo schedule ownership — 2026-09-20

William confirmed that only human operators may change the root Odoo Work
Schedule. AI staff and SAM may read it to build the display, but may not write
weekday Training cells or alter its row structure.

Live audit found historical machine writes to weekday cells through the Herald
Odoo bridge, including old unfinished-training rollover batches, plus the
September 18 guarded Farrier cleanup. Those operations used William's shared
Odoo integration identity, so Odoo's `write_uid` could misleadingly look human.
The last Harness-audited schedule-line write was September 9; the September 18
repair was a separate direct maintenance operation.

The boundary is now enforced at both layers:

- Odoo automation 24, `Populate Horese`, is inactive and can no longer add rows
  when the schedule is saved.
- Herald's guarded `/odoo/write` route denies the
  `x_work_schedule_line_a873e` model entirely; all seven weekday Training fields
  therefore have no AI/SAM write path.
- SAM continues reading schedule 22 and all horse needs. Its only retained Odoo
  mutation authority is to create completed Farrier/Veterinarian history and
  clear the matching horse-level boolean need flag after confirmed history.
- SAM completion details, checkmarks, and local carryovers remain in SAM's local
  SQLite/display layer and do not update Odoo Training cells.

Verification: a dry-run schedule-line write returned HTTP 403; the permitted
horse-level need-clear dry-run returned HTTP 200; SAM update and health both
returned `ok`. Automation disable was read back as `active: false`.

Recovery material is private on Herald at
`/Users/herald/backups/training-schedule-readonly-20260920/`, including the
pre-change Harness and Odoo automation/action snapshot. There is not yet a
separate Odoo maintenance identity. Exceptional schedule repairs remain blocked
unless William explicitly authorizes a maintenance operation; do not silently
use a human identity for them.

## Attempted replacement-schedule relationship repair — rolled back 2026-09-20

**Current status:** This entire relationship/view/reader migration was rolled
back after William found that it exposed old horses and lines that were not part
of Shawn's visible morning schedule. The description below is retained only as
incident history, not current operating state. Odoo relationships, labels,
sequences, and Studio view 10094 were restored from the pre-repair snapshots;
the newly created line 545 was detached. SAM and Herald readers were restored,
and no weekday code was reverted or changed. Final rollback verification found
the original 60 active rows, zero weekday-code differences from the snapshot,
healthy services, and a successful SAM refresh. Do not retry relationship
normalization until the intended current horse roster is established from a
human-authoritative source rather than inferred from hidden Odoo links.

William authorized a complete relationship repair after Shawn had rebuilt the
schedule following a failure. The replacement reused legacy named rows whose
`x_studio_horse` relationships still pointed at different horses, while the old
population automation appended additional relationship-only rows. SAM then
compounded the problem by treating the legacy `x_name` label as authoritative
and resolving a horse by text instead of using `x_studio_horse`.

The live schedule was privately snapshotted and repaired without changing any
weekday Training code. Named legacy rows for Mazy, Aurora, Frost, and Cosmo
were linked to their actual horse records; Feed AM/PM were detached from
incorrect horse relationships; displaced blank rows were safely reassigned to
Arti, Hondo, and Ruby; and one new correctly linked Kaleesi row was added. All
linked row labels were normalized to the horse's barn name.

Final verification found 60 active rows, 53 horse-linked rows, no duplicate
horse relationships, no missing active Training-status horses, no linked-name
mismatches, and zero weekday-code changes. SAM now treats `x_studio_horse` as
the authoritative identity and uses the legacy text label only for intentionally
unlinked rows such as Feed or lessons. Herald's deterministic training report
uses the same relationship-first rule. SAM refreshed successfully with all 61
rows and both services remained healthy. The guarded schedule-write path still
returns HTTP 403, and the old Odoo population automation remains disabled.

Private rollback snapshot:
`/Users/herald/backups/training-schedule-relationship-repair-20260920/before-20260920-230946.json`.

An initial view revision exposed both the corrected Horse Record and the legacy
label side by side, which made every row appear duplicated, and the two distinct
Odoo horse records sharing barn name Cosmo left two visible Cosmo rows. This was
corrected immediately: the active schedule row now points to Training-status
Cosmo (horse 121), the blank duplicate line 487 is detached from the schedule,
and the legacy label is shown only for intentionally unlinked task rows. Final
audit found zero duplicate horse IDs and zero duplicate displayed names. Backup:
`/Users/herald/backups/training-schedule-relationship-repair-20260920/before-cosmo-and-view-correction-20260920-231733.json`.

The underlying Odoo Studio defect was also corrected. View 10094 exposed the
legacy text field `x_name` as an editable column named **Horse**, while the real
many-to-one relationship `x_studio_horse` was completely hidden. Reworking a
schedule therefore changed only a horse-looking text label and silently left the
old horse ID attached. The former population automation compared those hidden
IDs, so it skipped some horses and appended apparent duplicates for others.

The effective Work Schedule form now exposes `x_studio_horse` as **Horse
Record**, limits it to existing horse records, and presents `x_name` explicitly
as a read-only display label. Odoo successfully compiled the resulting form
view. The separate, obsolete `New Lines` one-to-many model remains outside the
active Studio table and is not a SAM data source. The manual **Add Separator**
button remains valid: it deliberately creates an unlinked separator row. The
automatic `Populate Horese` automation remains disabled. View rollback:
`/Users/herald/backups/training-schedule-relationship-repair-20260920/odoo-view-10094-before-20260920-231624.json`.

