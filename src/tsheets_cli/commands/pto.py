"""PTO (time-off) commands - list and create PTO requests."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import typer
from rich.panel import Panel

from tsheets_cli.api import api_get, api_post, check_write_results
from tsheets_cli.output import console, format_duration, print_json, print_table
from tsheets_cli.resolve import resolve_user

app = typer.Typer(
    help="List and create PTO / time-off requests.",
    rich_markup_mode="rich",
)


def _parse_date(value: str, label: str) -> date:
    """Parse a YYYY-MM-DD string into a date, with a clear error on failure."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        console.print(
            f"[bold red]Invalid {label} date:[/] '{value}'\n"
            "[yellow]Use YYYY-MM-DD format (e.g. 2026-03-15).[/]"
        )
        raise typer.Exit(1)


def _get_current_user() -> tuple[int, str]:
    """Return (user_id, display_name) for the authenticated user."""
    data = api_get("/current_user")
    users = data.get("results", {}).get("users", {})
    if not users:
        console.print("[bold red]Could not determine current user.[/]")
        raise typer.Exit(1)
    uid = next(iter(users.keys()))
    u = users[uid]
    name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or str(uid)
    return int(uid), name


def _resolve_pto_type(type_name: str) -> tuple[int, str]:
    """Resolve a PTO type name to a (jobcode_id, display_name).

    PTO types in TSheets are jobcodes with type_code='pto'.
    Accepts partial, case-insensitive matches.
    """
    # If numeric, return as-is
    try:
        return int(type_name), type_name
    except ValueError:
        pass

    data = api_get("/jobcodes", params={"type": "pto"})
    jobcodes = data.get("results", {}).get("jobcodes", {})

    search = type_name.strip().lower()
    exact: list[tuple[int, str]] = []
    partial: list[tuple[int, str]] = []

    for jid, jc in jobcodes.items():
        jc_name = jc.get("name", "")
        if jc_name.lower() == search:
            exact.append((int(jid), jc_name))
        elif search in jc_name.lower():
            partial.append((int(jid), jc_name))

    matches = exact or partial

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        console.print(f"[yellow]Ambiguous PTO type '{type_name}'. Matches:[/]")
        for jid, name in matches:
            console.print(f"  {jid}: {name}")
        console.print("\n[yellow]Use the numeric ID or a more specific name.[/]")
        raise typer.Exit(1)
    else:
        if not jobcodes:
            console.print(
                "[bold red]No PTO jobcodes found.[/]\n"
                "[yellow]Your TSheets account may not have PTO types configured.\n"
                "Contact your administrator to set up PTO jobcodes.[/]"
            )
        else:
            console.print(f"[bold red]PTO type not found:[/] '{type_name}'")
            console.print("[yellow]Available PTO types:[/]")
            for jid, jc in jobcodes.items():
                console.print(f"  {jid}: {jc.get('name', '')}")
        raise typer.Exit(1)


def _build_entries(
    start_date: date,
    end_date: date,
    hours: int,
    skip_weekends: bool,
) -> dict[str, int]:
    """Build a dict of {YYYY-MM-DD: seconds} for each requested day."""
    entries: dict[str, int] = {}
    current = start_date
    while current <= end_date:
        if skip_weekends and current.weekday() >= 5:  # 5=Sat, 6=Sun
            current += timedelta(days=1)
            continue
        entries[current.strftime("%Y-%m-%d")] = hours * 3600
        current += timedelta(days=1)
    return entries


@app.command("list")
def list_pto(
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date filter (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date filter (YYYY-MM-DD)"),
    status: Optional[str] = typer.Option(
        None, "--status", help="Filter by status: pending, approved, denied, cancelled",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List PTO / time-off requests.

    Filter by user (name or ID), date range, and/or approval status.
    Shows request dates, total hours, and current status.

    [dim]Examples:
      tsheets pto list
      tsheets pto list --user "Jane Smith"
      tsheets pto list --status approved --start 2026-01-01 --end 2026-03-31[/]
    """
    params: dict = {}
    if user:
        params["user_ids"] = str(resolve_user(user))
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    if status:
        params["status"] = status

    data = api_get("/time_off_requests", params=params)

    if json_output:
        print_json(data)
        return

    requests = data.get("results", {}).get("time_off_requests", {})
    supplemental = data.get("supplemental_data", {})
    users_supp = supplemental.get("users", {})

    rows = []
    for rid, req in requests.items():
        uid = str(req.get("user_id", ""))
        user_info = users_supp.get(uid, {})
        user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or uid

        status_val = req.get("status", "")
        status_styled = {
            "pending": "[yellow]Pending[/]",
            "approved": "[green]Approved[/]",
            "denied": "[red]Denied[/]",
            "cancelled": "[dim]Cancelled[/]",
        }.get(status_val, status_val)

        # Get date range and total hours from entries
        entries = req.get("entries", {})
        dates = sorted(entries.keys()) if entries else []
        date_range = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else (dates[0] if dates else "-")

        # Sum up total hours across all entries
        total_hours = 0
        for _date, hrs in entries.items():
            try:
                total_hours += int(hrs)
            except (ValueError, TypeError):
                pass
        hours_display = format_duration(total_hours) if total_hours else "-"

        rows.append([
            str(rid),
            user_name,
            status_styled,
            date_range,
            hours_display,
            req.get("notes", "") or "",
        ])

    print_table(
        "PTO Requests",
        [
            ("ID", "cyan"),
            ("User", "bold"),
            ("Status", ""),
            ("Dates", ""),
            ("Hours", "green"),
            ("Notes", "dim"),
        ],
        rows,
    )


@app.command("request")
def create_pto_request(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    pto_type: str = typer.Option(
        ..., "--type", help="PTO type: name or ID (e.g. 'Vacation', 'Sick', or a jobcode ID)",
    ),
    user: Optional[str] = typer.Option(
        None, "--user", help="User name or ID (defaults to current user)",
    ),
    hours: int = typer.Option(8, "--hours", help="Hours per day (default: 8)"),
    notes: str = typer.Option("", "--notes", help="Reason / notes for the request"),
    skip_weekends: bool = typer.Option(
        True, "--skip-weekends/--include-weekends",
        help="Skip Sat/Sun (default: skip)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a PTO / time-off request.

    Submits a new time_off_request to TSheets for the specified user and date
    range.  Requires a PTO type (--type) which maps to a PTO jobcode in your
    TSheets account (e.g. "Vacation", "Sick Leave", "Personal").

    Examples:

        tsheets pto request --start 2026-03-16 --end 2026-03-20 --type Vacation

        tsheets pto request --start 2026-03-16 --end 2026-03-16 --type Sick --user "Jane Doe"

        tsheets pto request --start 2026-03-16 --end 2026-03-20 --type Vacation --hours 4
    """
    # ── Validate dates ──────────────────────────────────────────────
    start_date = _parse_date(start, "start")
    end_date = _parse_date(end, "end")

    if end_date < start_date:
        console.print(
            "[bold red]End date cannot be before start date.[/]\n"
            f"  Start: {start}  End: {end}"
        )
        raise typer.Exit(1)

    if hours < 1 or hours > 24:
        console.print("[bold red]Hours per day must be between 1 and 24.[/]")
        raise typer.Exit(1)

    # ── Resolve user ────────────────────────────────────────────────
    if user:
        user_id = resolve_user(user)
        user_display = user
    else:
        user_id, user_display = _get_current_user()

    # ── Resolve PTO type ────────────────────────────────────────────
    pto_type_id, pto_type_display = _resolve_pto_type(pto_type)

    # ── Build date entries ──────────────────────────────────────────
    entries = _build_entries(start_date, end_date, hours, skip_weekends)

    if not entries:
        console.print(
            "[bold red]No workdays in the selected range.[/]\n"
            "[yellow]All dates fall on weekends. "
            "Use --include-weekends to include them.[/]"
        )
        raise typer.Exit(1)

    # ── Submit request ──────────────────────────────────────────────
    request_data: dict = {
        "user_id": user_id,
        "time_off_request_type_id": pto_type_id,
        "entries": entries,
    }
    if notes:
        request_data["notes"] = notes

    data = api_post("/time_off_requests", {"data": [request_data]})

    if json_output:
        print_json(data)
        return

    # ── Confirmation output ─────────────────────────────────────────
    # Surface any per-item API rejection (HTTP 200 can still carry a failed item).
    results = check_write_results(data, "time_off_requests")

    if not results:
        console.print("[bold red]PTO request may not have been created.[/]")
        console.print(f"[dim]API response: {data}[/]")
        raise typer.Exit(1)

    for rid, req in results.items():
        status_val = req.get("status", "pending")
        status_styled = {
            "pending": "[yellow]Pending[/]",
            "approved": "[green]Approved[/]",
            "denied": "[red]Denied[/]",
        }.get(status_val, status_val)

        total_hours = len(entries) * hours
        date_list = sorted(entries.keys())
        date_range = (
            f"{date_list[0]} to {date_list[-1]}"
            if len(date_list) > 1
            else date_list[0]
        )

        summary = (
            f"[bold green]PTO Request Created[/]\n\n"
            f"  [bold]Request ID:[/]  {rid}\n"
            f"  [bold]User:[/]        {user_display}\n"
            f"  [bold]Type:[/]        {pto_type_display}\n"
            f"  [bold]Dates:[/]       {date_range}\n"
            f"  [bold]Days:[/]        {len(entries)}\n"
            f"  [bold]Hours/day:[/]   {hours}\n"
            f"  [bold]Total hours:[/] {total_hours}\n"
            f"  [bold]Status:[/]      {status_styled}\n"
        )
        if notes:
            summary += f"  [bold]Notes:[/]       {notes}\n"

        console.print(Panel(summary, title="PTO Confirmation", border_style="green"))
