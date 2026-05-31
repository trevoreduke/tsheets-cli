"""Timesheets commands - list and create time entries."""

from __future__ import annotations

from typing import Optional

import typer

from tsheets_cli.api import api_get, api_post, check_write_results
from tsheets_cli.output import console, format_date, format_duration, print_json, print_table
from tsheets_cli.resolve import resolve_jobcode, resolve_user

app = typer.Typer(
    help="List, create, and manage time entries.",
    rich_markup_mode="rich",
)


@app.command("list")
def list_timesheets(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID"),
    jobcode: Optional[str] = typer.Option(None, "--jobcode", help="Jobcode name or ID"),
    limit: int = typer.Option(50, help="Max results (max 200)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List timesheets with date range and optional filters.

    Returns time entries within the specified date range. Filter by user
    and/or jobcode using names or numeric IDs.

    [dim]Examples:
      tsheets timesheets list --start 2026-03-01 --end 2026-03-06
      tsheets timesheets list --start 2026-03-01 --end 2026-03-06 --user "Jane Smith"
      tsheets timesheets list --start 2026-03-01 --end 2026-03-01 --jobcode "Admin" --json[/]
    """
    params: dict = {
        "start_date": start,
        "end_date": end,
        "limit": min(limit, 200),
    }

    if user:
        params["user_ids"] = str(resolve_user(user))
    if jobcode:
        params["jobcode_ids"] = str(resolve_jobcode(jobcode))

    data = api_get("/timesheets", params=params)

    if json_output:
        print_json(data)
        return

    timesheets = data.get("results", {}).get("timesheets", {})
    # Gather supplemental data for display
    supplemental = data.get("supplemental_data", {})
    users_supp = supplemental.get("users", {})
    jobcodes_supp = supplemental.get("jobcodes", {})

    rows = []
    for tid, ts in timesheets.items():
        user_id = str(ts.get("user_id", ""))
        user_info = users_supp.get(user_id, {})
        user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or user_id

        jc_id = str(ts.get("jobcode_id", ""))
        jc_info = jobcodes_supp.get(jc_id, {})
        jc_name = jc_info.get("name", jc_id)

        duration = ts.get("duration", 0)
        on_clock = ts.get("on_the_clock", False)
        status = "[green]Active[/]" if on_clock else format_duration(duration)

        rows.append([
            str(tid),
            user_name,
            jc_name,
            format_date(ts.get("start")),
            format_date(ts.get("end")),
            status,
            ts.get("notes", "") or "",
        ])

    print_table(
        f"Timesheets ({start} to {end})",
        [
            ("ID", "cyan"),
            ("User", "bold"),
            ("Jobcode", ""),
            ("Start", ""),
            ("End", ""),
            ("Duration", "green"),
            ("Notes", "dim"),
        ],
        rows,
    )


@app.command("create")
def create_timesheet(
    user: str = typer.Option(..., "--user", help="User name or ID"),
    jobcode: str = typer.Option(..., "--jobcode", help="Jobcode name or ID"),
    start: str = typer.Option(..., "--start", help="Start time (ISO 8601, e.g. 2026-01-22T08:00:00-05:00)"),
    end: Optional[str] = typer.Option(None, "--end", help="End time (ISO 8601). Omit for active timer."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes for this entry"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a new timesheet entry.

    Creates a completed time entry or starts an active timer. Omit --end
    to create a running timer. User and jobcode accept names or IDs.

    [dim]Examples:
      tsheets timesheets create --user "Jane Smith" --jobcode "Admin" --start 2026-03-06T08:00:00-05:00 --end 2026-03-06T17:00:00-05:00
      tsheets timesheets create --user "Jane Smith" --jobcode "Admin" --start 2026-03-06T08:00:00-05:00  # starts timer[/]
    """
    user_id = resolve_user(user)
    jobcode_id = resolve_jobcode(jobcode)

    entry: dict = {
        "user_id": user_id,
        "jobcode_id": jobcode_id,
        "type": "regular",
        "start": start,
    }
    if end:
        entry["end"] = end
    if notes:
        entry["notes"] = notes

    data = api_post("/timesheets", {"data": [entry]})

    if json_output:
        print_json(data)
        return

    timesheets = check_write_results(data, "timesheets")
    for tid, ts in timesheets.items():
        status = ts.get("_status_extra", "")
        console.print(f"[green]Timesheet created:[/] ID {tid}")
        if ts.get("on_the_clock"):
            console.print("[yellow]Timer is now active.[/]")
        if status:
            console.print(f"[dim]{status}[/]")
