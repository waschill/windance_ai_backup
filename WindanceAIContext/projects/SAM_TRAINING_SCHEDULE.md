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
- Automatically updates once after 5:00 AM.
- Automatically commits at/after 11:55 PM if the day has not already been committed.

## URLs

- Schedule: `http://192.168.36.230:8088/`
- Wi-Fi Schedule: `http://192.168.36.29:8088/`
- Admin: `http://192.168.36.230:8088/admin`
- Health/status: `http://192.168.36.230:8088/api/status`

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
