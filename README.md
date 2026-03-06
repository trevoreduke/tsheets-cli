# TSheets CLI

A command-line tool for [TSheets / QuickBooks Time](https://tsheets.intuit.com) built with Python, [Typer](https://typer.tiangolo.com), and [Rich](https://rich.readthedocs.io).

Manage timesheets, clock in/out, run payroll reports, check who's on the clock, and more — all from your terminal.

## Features

- **Two-layer UX** — Quick shortcuts (`clock-in`, `whosin`, `today`) plus full API commands (`timesheets list`, `reports payroll`)
- **Name resolution** — Use employee and jobcode names instead of numeric IDs (`--user "Brad Tolbert"`)
- **Three output formats** — Rich tables (default), `--json` for scripting, `--csv` / `-o file.csv` for spreadsheets
- **Comprehensive error handling** — Clear, actionable messages for auth failures, network issues, and rate limits
- **Shell completion** — Tab completion for zsh, bash, and fish (`tsheets --install-completion`)
- **Single shared token** — One `TSHEETS_API_TOKEN` for the whole team

## Install

```bash
pip install git+https://github.com/trevoreduke/tsheets-cli.git
```

Or install from a `.whl` file:
```bash
pip install tsheets_cli-1.0.0-py3-none-any.whl
```

Requires Python 3.11+.

## Configuration

Set your TSheets API token (get it from your TSheets admin or [API add-ons page](https://tsheetsteam.tsheets.com/api-addons)):

```bash
export TSHEETS_API_TOKEN="S.your-token-here"
```

Add it to `~/.zshrc` or `~/.bashrc` so it persists across sessions.

Verify with:
```bash
tsheets me
```

## Quick Start

```bash
tsheets whosin                                    # who's on the clock right now?
tsheets clock-in --jobcode "Admin"                # start a timer
tsheets today                                     # check your hours today
tsheets clock-out                                 # stop the timer
tsheets payroll                                   # last week's payroll report
tsheets reports totals -o totals.csv              # export current totals to CSV
```

---

## Command Reference

### Shortcuts

| Command | Description |
|---------|-------------|
| `tsheets me` | Show current authenticated user |
| `tsheets clock-in --jobcode NAME` | Start a timer (auto-stops existing timer) |
| `tsheets clock-out` | Stop the running timer |
| `tsheets today [--user NAME]` | Hours worked today |
| `tsheets week [--user NAME]` | Weekly summary (Mon-today) |
| `tsheets whosin` | Who's currently clocked in |
| `tsheets locate --user NAME` | Last known GPS location |
| `tsheets payroll [--start --end]` | Payroll report (defaults to last complete week) |

### API Commands

| Command | Description |
|---------|-------------|
| `tsheets users list` | List all employees |
| `tsheets timesheets list --start DATE --end DATE` | List time entries |
| `tsheets timesheets create --user NAME --jobcode NAME --start DT` | Create a time entry |
| `tsheets jobcodes list` | List all jobcodes (projects/tasks) |
| `tsheets jobcodes create --name NAME` | Create a new jobcode |
| `tsheets projects list` | List all projects |
| `tsheets reports payroll --start DATE --end DATE` | Payroll report |
| `tsheets reports totals` | Current pay period totals |
| `tsheets reports current-all` | Detailed clock status for everyone |
| `tsheets reports project-estimate` | Project estimate vs actual |
| `tsheets reports project --start DATE --end DATE` | Project time breakdown |
| `tsheets pto list` | List PTO / time-off requests |
| `tsheets pto request --start DATE --end DATE --type TYPE` | Submit a PTO request |
| `tsheets geo list --user NAME --start DATE --end DATE` | GPS tracking data |
| `tsheets geo latest --user NAME` | Most recent GPS location |
| `tsheets geofences list` | Geofence boundary configurations |

---

## Examples with Real Output

### Who's on the clock?

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

### Clock in and out

```
$ tsheets clock-in --jobcode "Admin" --notes "Morning tasks"
Clocked in! Timer ID: 894721553
Jobcode: Admin | Started at: 2026-03-06T14:30:00+00:00
Timer is now running.

$ tsheets clock-out
Clocked out! Timer ID: 894721553
Jobcode: Admin | Duration: 2h 15m
```

If you clock in while already on the clock, the existing timer is stopped automatically.

### List employees

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
│ 1377491 │ Trevor Duke           │ trevor@thomasduke.com  │ -        │ Active │
│ ...     │ (16 total)            │                        │          │        │
└─────────┴───────────────────────┴────────────────────────┴──────────┴────────┘
```

### CSV export

```
$ tsheets reports totals --csv
Name,Regular,Overtime,Double Time,PTO,Today,On Clock
Jamal Allen,0:00,0:00,0:00,0:00,7h 12m,Liberty Center Driving (2h 49m)
Jon Bielicki,0:00,0:00,0:00,0:00,0:00,No
...

$ tsheets reports totals -o totals.csv
Wrote 16 rows to totals.csv

$ tsheets payroll -o payroll.csv
Wrote 12 rows to payroll.csv
```

### JSON output

```bash
# Pipe to jq for scripting
tsheets users list --json | jq '.results.users | keys[]'

# Count people on the clock
tsheets whosin --json | jq '[.results.current_totals | to_entries[] | select(.value.on_the_clock)] | length'

# Save raw API response
tsheets reports payroll --start 2026-02-24 --end 2026-03-02 --json > payroll.json
```

---

## Name Resolution

Use employee names and jobcode names instead of numeric IDs. The CLI resolves them automatically:

```bash
tsheets timesheets list --start 2026-03-06 --end 2026-03-06 --user "Brad Tolbert"
tsheets clock-in --jobcode "Admin"
tsheets locate --user "Jamal Allen"
tsheets payroll --user "Don Harris"
```

Numeric IDs also work: `--user 2487146`

If a name is ambiguous, you'll see all matches and can pick the right one.

---

## Error Messages

**Missing token:**
```
$ tsheets me
Error: TSHEETS_API_TOKEN environment variable is not set.

To fix, set your TSheets/QuickBooks Time API token:
  export TSHEETS_API_TOKEN='S.xxxxxxxxxxxxxxxxxxxx'

Get your token from: https://tsheetsteam.tsheets.com/api-addons
Or ask your TSheets admin for the shared company API token.
```

**Invalid token:**
```
Authentication failed (401 Unauthorized).
  Token in use: S.6_...76a6
Possible causes:
  1. Token is invalid or was revoked
  2. Token has expired
  3. Token was copy-pasted with extra whitespace or quotes
```

**Network error:**
```
DNS resolution failed. Could not resolve rest.tsheets.com.
Check your internet connection and try again.
```

---

## Full Command Tree

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

All commands support `--json` and `--help`. Report commands additionally support `--csv` and `--output FILE`.

---

## Development

```bash
git clone https://github.com/trevoreduke/tsheets-cli.git
cd tsheets-cli
python -m venv .venv && source .venv/bin/activate
pip install -e .
tsheets --help
```

## License

MIT
