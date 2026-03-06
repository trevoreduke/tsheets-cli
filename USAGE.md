# TSheets CLI - Usage Guide

A command-line tool for TSheets / QuickBooks Time. Two layers: **shortcut commands** for daily workflows and **API commands** for full TSheets access.

---

## Setup

```bash
# Install from git
pip install git+https://github.com/trevoreduke/tsheets-cli.git

# Set your API token (add to ~/.bashrc or ~/.zshrc)
export TSHEETS_API_TOKEN="S.abc123..."

# Verify it works
tsheets me
```

All commands support `--json` for machine-readable output and `--help` for usage details.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `tsheets me` | Show current authenticated user |
| `tsheets clock-in --jobcode "Admin"` | Start a timer |
| `tsheets clock-out` | Stop the running timer |
| `tsheets today` | Hours worked today |
| `tsheets week` | Weekly summary (Mon-today) |
| `tsheets whosin` | Who's currently on the clock |
| `tsheets locate --user "Jane Smith"` | Last known GPS location |
| `tsheets payroll` | Payroll report (last complete week) |

---

## Shortcut Commands

### Check who you are

```
$ tsheets me

                      Current User
┏━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ID      ┃ Name          ┃ Email                 ┃ Status ┃ Last Active         ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 3481022 │ Trevor Duke   │ trevor@thomasduke.com │ Active │ 2026-03-06T14:22:00 │
└─────────┴───────────────┴───────────────────────┴────────┴─────────────────────┘
```

### Clock in / Clock out

```
$ tsheets clock-in --jobcode "Admin" --notes "Morning tasks"

Clocked in! Timer ID: 894721553
Jobcode: Admin | Started at: 2026-03-06T14:30:00+00:00
Timer is now running.
```

```
$ tsheets clock-out

Clocked out! Timer ID: 894721553
Jobcode: Admin | Duration: 2h 15m
```

If you clock in while already on the clock, the existing timer is stopped automatically:

```
$ tsheets clock-in --jobcode "Leasing"

Stopped existing timer (ID: 894721553, duration: 2h 15m).
Clocked in! Timer ID: 894721580
Jobcode: Leasing | Started at: 2026-03-06T16:45:00+00:00
Timer is now running.
```

### Today's hours

```
$ tsheets today

                         Today (2026-03-06)
┏━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Jobcode   ┃ Start ┃ End   ┃ Duration ┃ Notes           ┃
┡━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Admin     │ 08:00 │ 10:30 │ 2h 30m   │ Morning tasks   │
│ Leasing   │ 10:45 │ 12:00 │ 1h 15m   │ Showing at 1700 │
│ Admin     │ 13:00 │ now   │ Active   │                 │
└───────────┴───────┴───────┴──────────┴─────────────────┘

Total: 5h 02m
```

Check another user's day:

```
$ tsheets today --user "Jane Smith"
```

### Weekly summary

```
$ tsheets week

               This Week (2026-03-02 to 2026-03-06)
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ Date       ┃ Day       ┃ Hours  ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ 2026-03-02 │ Monday    │ 8h 30m │
│ 2026-03-03 │ Tuesday   │ 9h 00m │
│ 2026-03-04 │ Wednesday │ 8h 15m │
│ 2026-03-05 │ Thursday  │ 7h 45m │
│ 2026-03-06 │ Friday    │ 5h 02m │
└────────────┴───────────┴────────┘

Week Total: 38h 32m
```

### Who's on the clock

```
$ tsheets whosin

                      Currently Clocked In
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Name           ┃ Jobcode   ┃ Shift Duration ┃ Day Total ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Trevor Duke    │ Admin     │ 2h 02m         │ 5h 02m    │
│ Jane Smith     │ Leasing   │ 3h 45m         │ 7h 15m    │
│ Mike Johnson   │ Maint.    │ 5h 30m         │ 5h 30m    │
└────────────────┴───────────┴────────────────┴───────────┘
```

### Locate a user (GPS)

```
$ tsheets locate --user "Jane Smith"

Last known location for user 3481099:
  Coordinates: 42.5584, -83.1781 (accuracy: 12m)
  Timestamp:   2026-03-06 14:18:00
  Google Maps: https://www.google.com/maps?q=42.5584,-83.1781
```

### Quick payroll report

Defaults to the last complete Mon-Sun week:

```
$ tsheets payroll

                Payroll Report (2026-02-24 to 2026-03-02)
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┓
┃ Employee       ┃ Regular ┃ Overtime ┃ Double Time ┃ PTO   ┃ Total   ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━┩
│ Jane Smith     │ 40h 00m │ 2h 30m  │ 0h 00m      │ 0h 00m│ 42h 30m │
│ Mike Johnson   │ 38h 15m │ 0h 00m  │ 0h 00m      │ 8h 00m│ 38h 15m │
│ Trevor Duke    │ 40h 00m │ 4h 45m  │ 0h 00m      │ 0h 00m│ 44h 45m │
│ TOTAL          │ 118h 15m│ 7h 15m  │ 0h 00m      │ 8h 00m│ 125h 30m│
└────────────────┴─────────┴─────────┴─────────────┴───────┴─────────┘
```

Custom date range or single user:

```
$ tsheets payroll --start 2026-02-01 --end 2026-02-28 --user "Jane Smith"
```

---

## API Commands

### Users

```bash
# List all active users
tsheets users list

# Include inactive users
tsheets users list --active both

# JSON output for scripting
tsheets users list --json
```

```
$ tsheets users list

                              Users
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ ID      ┃ Name           ┃ Email                   ┃ Group ID ┃ Status ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ 3481022 │ Trevor Duke    │ trevor@thomasduke.com   │ 98541    │ Active │
│ 3481099 │ Jane Smith     │ jane@thomasduke.com     │ 98541    │ Active │
│ 3481155 │ Mike Johnson   │ mike@thomasduke.com     │ 98542    │ Active │
└─────────┴────────────────┴─────────────────────────┴──────────┴────────┘
```

### Timesheets

```bash
# List time entries for a date range
tsheets timesheets list --start 2026-03-01 --end 2026-03-06

# Filter by user and jobcode (names or IDs work)
tsheets timesheets list --start 2026-03-06 --end 2026-03-06 --user "Jane Smith" --jobcode "Admin"

# Create a completed time entry
tsheets timesheets create --user "Jane Smith" --jobcode "Admin" \
  --start 2026-03-06T08:00:00-05:00 --end 2026-03-06T17:00:00-05:00 \
  --notes "Full day admin work"

# Create an active timer (omit --end)
tsheets timesheets create --user "Jane Smith" --jobcode "Leasing" \
  --start 2026-03-06T08:00:00-05:00
```

```
$ tsheets timesheets list --start 2026-03-06 --end 2026-03-06

                      Timesheets (2026-03-06 to 2026-03-06)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ ID         ┃ User         ┃ Jobcode ┃ Start               ┃ End                 ┃ Duration ┃ Notes          ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 894721553  │ Trevor Duke  │ Admin   │ 2026-03-06 08:00:00 │ 2026-03-06 10:30:00 │ 2h 30m   │ Morning tasks  │
│ 894721580  │ Trevor Duke  │ Leasing │ 2026-03-06 10:45:00 │ 2026-03-06 12:00:00 │ 1h 15m   │ Showing        │
│ 894721601  │ Jane Smith   │ Admin   │ 2026-03-06 08:00:00 │ 2026-03-06 17:00:00 │ 9h 00m   │ Full day       │
└────────────┴──────────────┴─────────┴─────────────────────┴─────────────────────┴──────────┴────────────────┘
```

### Jobcodes

```bash
# List all active jobcodes
tsheets jobcodes list

# Create a new jobcode
tsheets jobcodes create --name "New Project"

# Create a sub-jobcode under a parent (by name)
tsheets jobcodes create --name "Phase 1" --parent "New Project" --short-code P1

# Non-billable jobcode
tsheets jobcodes create --name "Internal Meeting" --no-billable
```

```
$ tsheets jobcodes list

                               Jobcodes
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ ID       ┃ Name               ┃ Parent ID ┃ Billable ┃ Short Code ┃ Status ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ 18265410 │ Admin              │ 0         │ No       │ ADM        │ Active │
│ 18265425 │ Leasing            │ 0         │ Yes      │ LSG        │ Active │
│ 18265430 │ Maintenance        │ 0         │ No       │ MNT        │ Active │
│ 18265448 │ Property Mgmt      │ 0         │ Yes      │ PM         │ Active │
│ 18265460 │ New Project        │ 0         │ Yes      │            │ Active │
│ 18265461 │ Phase 1            │ 18265460  │ Yes      │ P1         │ Active │
└──────────┴────────────────────┴───────────┴──────────┴────────────┴────────┘
```

### Projects

```bash
# List all projects
tsheets projects list

# Include inactive projects
tsheets projects list --active both
```

```
$ tsheets projects list

                          Projects
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID      ┃ Name                 ┃ Description             ┃ Status  ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ 5012    │ Office Build-Out     │ Suite 200 renovation    │ active  │
│ 5018    │ Website Redesign     │ Company website refresh │ active  │
│ 5024    │ 1700 Big Beaver Maint│ Ongoing maintenance     │ active  │
└─────────┴──────────────────────┴─────────────────────────┴─────────┘
```

### Reports

```bash
# Payroll report
tsheets reports payroll --start 2026-02-24 --end 2026-03-02

# Current period totals (all users)
tsheets reports totals

# Only users currently on the clock
tsheets reports totals --on-the-clock

# Current all - detailed clock status for everyone
tsheets reports current-all

# Project estimate vs actual
tsheets reports project-estimate
tsheets reports project-estimate --project "Website Redesign"

# Project time report with breakdowns
tsheets reports project --start 2026-01-01 --end 2026-03-06
tsheets reports project --project "Office Build-Out" --start 2026-02-01 --end 2026-02-28
```

```
$ tsheets reports totals

                          Current Period Totals
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Name           ┃ Regular ┃ Overtime ┃ Double Time ┃ PTO    ┃ Today  ┃ On Clock          ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Trevor Duke    │ 38h 32m │ 0h 00m  │ 0h 00m      │ 0h 00m │ 5h 02m │ Admin (2h 02m)    │
│ Jane Smith     │ 36h 15m │ 0h 00m  │ 0h 00m      │ 0h 00m │ 7h 15m │ Leasing (3h 45m)  │
│ Mike Johnson   │ 32h 00m │ 0h 00m  │ 0h 00m      │ 8h 00m │ 5h 30m │ Maint. (5h 30m)   │
└────────────────┴─────────┴─────────┴─────────────┴────────┴────────┴───────────────────┘

Period Totals: Regular: 106h 47m | OT: 0h 00m | DT: 0h 00m | PTO: 8h 00m
```

```
$ tsheets reports project-estimate

                  Project Estimate vs Actual
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Project ID ┃ Project              ┃ Estimated ┃ Actual  ┃ % Complete ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ 5012       │ Office Build-Out     │ 200h 00m  │ 142h 30m│ 71%        │
│ 5018       │ Website Redesign     │ 80h 00m   │ 65h 15m │ 82%        │
└────────────┴──────────────────────┴───────────┴─────────┴────────────┘
```

### PTO / Time-Off

```bash
# List all PTO requests
tsheets pto list

# Filter by user and status
tsheets pto list --user "Jane Smith" --status approved

# Filter by date range
tsheets pto list --start 2026-01-01 --end 2026-06-30

# Request vacation (weekdays only, 8h/day by default)
tsheets pto request --start 2026-03-16 --end 2026-03-20 --type Vacation \
  --notes "Spring break trip"

# Request a half-day
tsheets pto request --start 2026-03-16 --end 2026-03-16 --type "Sick" --hours 4

# Include weekends
tsheets pto request --start 2026-03-14 --end 2026-03-16 --type Vacation --include-weekends
```

```
$ tsheets pto list

                              PTO Requests
┏━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ ID      ┃ User          ┃ Status   ┃ Dates                       ┃ Hours   ┃ Notes             ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ 220145  │ Jane Smith    │ Approved │ 2026-03-16 to 2026-03-20    │ 40h 00m │ Spring break trip │
│ 220189  │ Mike Johnson  │ Pending  │ 2026-04-01 to 2026-04-03    │ 24h 00m │ Family event      │
│ 220201  │ Trevor Duke   │ Approved │ 2026-02-14                  │ 4h 00m  │ Dentist appt      │
└─────────┴───────────────┴──────────┴─────────────────────────────┴─────────┴───────────────────┘
```

```
$ tsheets pto request --start 2026-03-16 --end 2026-03-20 --type Vacation --notes "Spring break"

╭──────────────── PTO Confirmation ────────────────╮
│ PTO Request Created                              │
│                                                  │
│   Request ID:  220210                            │
│   User:        Trevor Duke                       │
│   Type:        Vacation                          │
│   Dates:       2026-03-16 to 2026-03-20          │
│   Days:        5                                 │
│   Hours/day:   8                                 │
│   Total hours: 40                                │
│   Status:      Pending                           │
│   Notes:       Spring break                      │
╰──────────────────────────────────────────────────╯
```

### Geolocation

```bash
# List GPS points for a user/date range
tsheets geo list --user "Jane Smith" --start 2026-03-06 --end 2026-03-06

# Show most recent GPS points
tsheets geo latest --user "Jane Smith"
tsheets geo latest --user "Jane Smith" --limit 5

# List geofence configurations
tsheets geofences list
```

```
$ tsheets geo latest --user "Jane Smith" --limit 3

              Latest Geolocations (User 3481099)
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Coordinates          ┃ Accuracy ┃ Timestamp           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 42.5584, -83.1781    │ 12m      │ 2026-03-06 14:18:00 │
│ 42.5580, -83.1775    │ 8m       │ 2026-03-06 14:12:00 │
│ 42.5541, -83.1820    │ 15m      │ 2026-03-06 13:45:00 │
└──────────────────────┴──────────┴─────────────────────┘

Google Maps: https://www.google.com/maps?q=42.5584,-83.1781
```

---

## Name Resolution

You can use **names instead of numeric IDs** everywhere. The CLI resolves them automatically:

```bash
# These are equivalent:
tsheets timesheets list --start 2026-03-06 --end 2026-03-06 --user 3481099
tsheets timesheets list --start 2026-03-06 --end 2026-03-06 --user "Jane Smith"

# Jobcodes by name:
tsheets clock-in --jobcode "Admin"
tsheets clock-in --jobcode 18265410

# Partial matches work for PTO types:
tsheets pto request --start 2026-03-16 --end 2026-03-20 --type Vac
```

If a name is ambiguous, you'll see all matches and can pick the right one.

---

## JSON Output

Every command supports `--json` for scripting and piping:

```bash
# Pipe to jq
tsheets users list --json | jq '.results.users | keys[]'

# Save report
tsheets reports payroll --start 2026-02-24 --end 2026-03-02 --json > payroll.json

# Use in scripts
ACTIVE=$(tsheets whosin --json | jq '.results.current_totals | to_entries | map(select(.value.on_the_clock == true)) | length')
echo "$ACTIVE people on the clock"
```

---

## Error Handling

Missing token:
```
$ tsheets me
Error: TSHEETS_API_TOKEN environment variable is not set.

Fix: export TSHEETS_API_TOKEN="S.your_token_here"
     Add it to your ~/.bashrc or ~/.zshrc to persist across sessions.
```

Bad token:
```
$ tsheets me
Error: Authentication failed (HTTP 401).

Your API token is invalid or expired.
Fix: Verify your token at https://rest.tsheets.com and update TSHEETS_API_TOKEN.
```

Network error:
```
$ tsheets me
Error: Could not connect to https://rest.tsheets.com/api/v1/current_user

Check your internet connection and try again.
```

---

## Command Structure

```
tsheets
├── me                          Show current user
├── clock-in  --jobcode         Start timer
├── clock-out                   Stop timer
├── today     [--user]          Today's hours
├── week      [--user]          Weekly summary
├── whosin                      Who's on the clock
├── locate    --user [--date]   Last GPS location
├── payroll   [--start --end]   Quick payroll report
│
├── users
│   └── list  [--active]        List employees
├── timesheets
│   ├── list  --start --end     List time entries
│   └── create --user --jobcode --start [--end]
├── jobcodes
│   ├── list  [--active]        List jobcodes
│   └── create --name [--parent]
├── projects
│   └── list  [--active]        List projects
├── reports
│   ├── payroll --start --end   Payroll report
│   ├── totals                  Current period totals
│   ├── current-all             Detailed clock status
│   ├── project-estimate        Estimate vs actual
│   └── project --start --end   Project time breakdown
├── pto
│   ├── list  [--user --status] List PTO requests
│   └── request --start --end --type
├── geo
│   ├── list  --user --start --end
│   └── latest --user
└── geofences
    └── list                    Geofence configs
```
