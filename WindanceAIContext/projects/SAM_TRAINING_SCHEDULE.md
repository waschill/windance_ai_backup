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
