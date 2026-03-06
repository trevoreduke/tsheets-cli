"""TSheets CLI - main entry point with Typer app and command registration."""

from __future__ import annotations

from typing import Optional

import typer

from tsheets_cli import __version__
from tsheets_cli.api import api_get
from tsheets_cli.commands import geo, jobcodes, projects, pto, reports, shortcuts, timesheets, users
from tsheets_cli.output import console, print_json, print_table

# ── Main app ──────────────────────────────────────────────────────────
app = typer.Typer(
    name="tsheets",
    help=(
        "[bold]TSheets CLI[/] — Command-line tool for TSheets / QuickBooks Time API.\n\n"
        "Requires [cyan]TSHEETS_API_TOKEN[/] environment variable to be set.\n\n"
        "[bold]Shortcuts[/] (common workflows):\n"
        "  [green]clock-in[/]   Start a timer          [green]clock-out[/]  Stop the timer\n"
        "  [green]today[/]      Hours worked today      [green]week[/]       Weekly summary\n"
        "  [green]whosin[/]     Who's on the clock      [green]locate[/]     Last GPS location\n"
        "  [green]payroll[/]    Quick payroll report\n\n"
        "[bold]API Commands[/] (full TSheets API access):\n"
        "  [cyan]users[/]      List employees           [cyan]timesheets[/] Time entries\n"
        "  [cyan]jobcodes[/]   Projects & tasks          [cyan]projects[/]   Project records\n"
        "  [cyan]reports[/]    Payroll & totals          [cyan]pto[/]        Time-off requests\n"
        "  [cyan]geo[/]        GPS geolocation           [cyan]geofences[/]  Geofence configs\n\n"
        "[dim]All commands support --json for machine-readable output.\n"
        "Use --help on any subcommand for details and examples.[/]"
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"tsheets-cli v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """[bold]TSheets CLI[/] — Command-line tool for TSheets / QuickBooks Time API."""


# ── Layer 1: Raw API subcommands ──────────────────────────────────────

# Register command groups
app.add_typer(users.app, name="users", help="List and manage users in the organization.")
app.add_typer(timesheets.app, name="timesheets", help="List, create, and manage time entries.")
app.add_typer(jobcodes.app, name="jobcodes", help="List and create jobcodes (projects/tasks).")
app.add_typer(projects.app, name="projects", help="List and view project records.")
app.add_typer(reports.app, name="reports", help="Payroll, current totals, and project reports.")
app.add_typer(pto.app, name="pto", help="List and create PTO / time-off requests.")
app.add_typer(geo.app, name="geo", help="GPS geolocation data and tracking.")
app.add_typer(geo.geofences_app, name="geofences", help="Geofence boundary configurations.")


# ── Top-level: current user ───────────────────────────────────────────

@app.command("me")
def me(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show the current authenticated user.

    Displays the user associated with the API token, including name,
    email, and account status. Useful for verifying your auth setup.

    [dim]Example:  tsheets me[/]
    """
    data = api_get("/current_user")

    if json_output:
        print_json(data)
        return

    user_data = data.get("results", {}).get("users", {})
    rows = []
    for uid, u in user_data.items():
        rows.append([
            str(uid),
            f"{u.get('first_name', '')} {u.get('last_name', '')}".strip(),
            u.get("email", "-"),
            "Active" if u.get("active") else "Inactive",
            u.get("last_active", "-") or "-",
        ])

    print_table(
        "Current User",
        [
            ("ID", "cyan"),
            ("Name", "bold"),
            ("Email", ""),
            ("Status", "green"),
            ("Last Active", "dim"),
        ],
        rows,
    )


# ── Layer 2: Shortcut commands ────────────────────────────────────────

app.command("clock-in")(shortcuts.clock_in)
app.command("clock-out")(shortcuts.clock_out)
app.command("today")(shortcuts.today)
app.command("week")(shortcuts.week)
app.command("whosin")(shortcuts.whosin)
app.command("locate")(shortcuts.locate)
app.command("payroll")(shortcuts.payroll)
