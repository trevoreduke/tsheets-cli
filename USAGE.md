# TSheets CLI - Quick Reference

Command-line tool for TSheets / QuickBooks Time. **Shortcuts** for daily workflows + **API commands** for full access.

## Setup

```bash
pip install git+https://github.com/trevoreduke/tsheets-cli.git
export TSHEETS_API_TOKEN="S.your-token-here"    # add to ~/.zshrc for persistence
tsheets me                                       # verify it works
```

All commands support `--json` for machine output, `--help` for usage. Report commands also support `--csv` and `--output FILE`.

---

## Shortcuts

### tsheets me
```
$ tsheets me

                  Current User
┏━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID      ┃ Name        ┃ Email                ┃ Status ┃ Last Active          ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 1377491 │ Trevor Duke │ trevor@thomasduke.c… │ Active │ 2026-02-25 16:38     │
└─────────┴─────────────┴──────────────────────┴────────┴──────────────────────┘
```

### tsheets clock-in / clock-out
```
$ tsheets clock-in --jobcode "Admin" --notes "Morning tasks"
Clocked in! Timer ID: 894721553
Jobcode: Admin | Started at: 2026-03-06T14:30:00+00:00
Timer is now running.

$ tsheets clock-out
Clocked out! Timer ID: 894721553
Jobcode: Admin | Duration: 2h 15m
```

### tsheets whosin
```
$ tsheets whosin

                     Currently Clocked In
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Name           ┃ Jobcode                ┃ Shift Duration ┃ Day Total ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Jamal Allen    │ Liberty Center Driving │ 2h 49m         │ 7h 12m    │
│ Branislav Ilic │ Kercheval WORK Time    │ 2h 42m         │ 6h 52m    │
│ Alex Kunets    │ Freedom Plaza Drive    │ 4h 36m         │ 4h 36m    │
│ David Robinson │ Liberty Center Work    │ 7h 17m         │ 7h 17m    │
│ Brad Tolbert   │ Haggerty Pointe Work   │ 59m            │ 6h 26m    │
└────────────────┴────────────────────────┴────────────────┴───────────┘
```

### tsheets today / week
```
$ tsheets today                        # your hours today
$ tsheets today --user "Brad Tolbert"  # someone else's hours
$ tsheets week                         # Mon-today summary
$ tsheets week --user "Alex Kunets"
```

### tsheets locate
```
$ tsheets locate --user "Jamal Allen"
Last known location for user 3565216:
  Coordinates: 42.5584, -83.1781 (accuracy: 12m)
  Timestamp:   2026-03-06 14:18
  Google Maps: https://www.google.com/maps?q=42.5584,-83.1781
```

### tsheets payroll
```
$ tsheets payroll                                              # last complete week
$ tsheets payroll --start 2026-02-24 --end 2026-03-02         # custom range
$ tsheets payroll --csv                                        # CSV to stdout
$ tsheets payroll -o payroll.csv                               # save to file
```

---

## API Commands

### tsheets users list
```
$ tsheets users list

                                Users
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ ID      ┃ Name                  ┃ Email                  ┃ Group ID ┃ Status ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ 3565216 │ Jamal Allen           │ jallen@thomasduke.com  │ -        │ Active │
│ 2126336 │ Branislav Ilic        │ bilich@thomasduke.com  │ -        │ Active │
│ 2917972 │ Alex Kunets           │ akunets@thomasduke.com │ -        │ Active │
│ 2487148 │ Don Harris            │ dharris@thomasduke.com │ -        │ Active │
│ 2487146 │ Brad Tolbert          │ btolbert@thomasduke.c… │ -        │ Active │
│ ...     │ (16 total)            │                        │          │        │
└─────────┴───────────────────────┴────────────────────────┴──────────┴────────┘

$ tsheets users list --active both     # include inactive users
```

### tsheets timesheets
```
$ tsheets timesheets list --start 2026-03-06 --end 2026-03-06
$ tsheets timesheets list --start 2026-03-01 --end 2026-03-06 --user "Brad Tolbert"
$ tsheets timesheets create --user "Brad Tolbert" --jobcode "Admin" \
    --start 2026-03-06T08:00:00-05:00 --end 2026-03-06T17:00:00-05:00 \
    --notes "Full day admin"
```

### tsheets jobcodes
```
$ tsheets jobcodes list                                        # all active jobcodes
$ tsheets jobcodes create --name "New Project"                 # top-level
$ tsheets jobcodes create --name "Phase 1" --parent "New Project" --short-code P1
```

### tsheets projects list
```
$ tsheets projects list
$ tsheets projects list --active both
```

### tsheets reports
```
$ tsheets reports payroll --start 2026-02-24 --end 2026-03-02
$ tsheets reports payroll --start 2026-02-24 --end 2026-03-02 --user "Don Harris"
$ tsheets reports totals                           # current pay period totals
$ tsheets reports totals --on-the-clock            # only clocked-in users
$ tsheets reports current-all                      # detailed clock status
$ tsheets reports project-estimate                 # estimate vs actual
$ tsheets reports project --start 2026-01-01 --end 2026-03-06
```

### tsheets pto
```
$ tsheets pto list
$ tsheets pto list --user "Licia Miller" --status approved
$ tsheets pto request --start 2026-03-16 --end 2026-03-20 --type Vacation \
    --notes "Spring break"
```

### tsheets geo / geofences
```
$ tsheets geo list --user "Jamal Allen" --start 2026-03-06 --end 2026-03-06
$ tsheets geo latest --user "Alex Kunets"
$ tsheets geofences list
```

---

## Output Formats

### Table (default)
```
$ tsheets whosin
```

### JSON (for scripting)
```
$ tsheets users list --json | jq '.results.users | keys[]'
$ tsheets whosin --json | jq '[.results.current_totals | to_entries[] | select(.value.on_the_clock)] | length'
```

### CSV (for spreadsheets)
```
$ tsheets reports totals --csv
Name,Regular,Overtime,Double Time,PTO,Today,On Clock
Jamal Allen,0:00,0:00,0:00,0:00,7h 12m,Liberty Center Driving (2h 49m)
Jon Bielicki,0:00,0:00,0:00,0:00,0:00,No
...

$ tsheets reports totals -o totals.csv
Wrote 16 rows to totals.csv
```

---

## Name Resolution

Use names instead of numeric IDs everywhere:
```
$ tsheets timesheets list --start 2026-03-06 --end 2026-03-06 --user "Brad Tolbert"
$ tsheets clock-in --jobcode "Admin"
$ tsheets locate --user "Jamal Allen"
```
Numeric IDs also work: `--user 2487146`

---

## Errors

**Missing token:**
```
$ tsheets me
Error: TSHEETS_API_TOKEN environment variable is not set.

To fix, set your TSheets/QuickBooks Time API token:
  export TSHEETS_API_TOKEN='S.xxxxxxxxxxxxxxxxxxxx'
```

**Bad token:**
```
Authentication failed (401 Unauthorized).
  Token in use: S.6_...76a6
Possible causes:
  1. Token is invalid or was revoked
  2. Token has expired
```

**Network error:**
```
DNS resolution failed. Could not resolve rest.tsheets.com.
Check your internet connection and try again.
```

---

## Command Tree

```
tsheets
├── me                          Show current user
├── clock-in  --jobcode         Start timer
├── clock-out                   Stop timer
├── today     [--user]          Today's hours
├── week      [--user]          Weekly summary
├── whosin                      Who's on the clock
├── locate    --user            Last GPS location
├── payroll   [--start --end]   Quick payroll report
│
├── users
│   └── list  [--active]
├── timesheets
│   ├── list  --start --end [--user] [--jobcode]
│   └── create --user --jobcode --start [--end] [--notes]
├── jobcodes
│   ├── list
│   └── create --name [--parent] [--short-code] [--no-billable]
├── projects
│   └── list  [--active]
├── reports
│   ├── payroll --start --end [--user] [--csv] [-o FILE]
│   ├── totals [--on-the-clock] [--csv] [-o FILE]
│   ├── current-all [--csv] [-o FILE]
│   ├── project-estimate [--project] [--csv] [-o FILE]
│   └── project [--start --end] [--project] [--user] [--csv] [-o FILE]
├── pto
│   ├── list [--user] [--status]
│   └── request --start --end --type [--notes]
├── geo
│   ├── list --user --start --end
│   └── latest --user
└── geofences
    └── list
```
