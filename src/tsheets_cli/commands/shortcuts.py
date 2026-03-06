"""Shortcut commands - clock-in, clock-out, today, week, whosin, locate, payroll."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import typer

from rich.console import Console

from tsheets_cli.api import api_get, api_post, api_put, api_delete
from tsheets_cli.output import console, format_duration, print_json, print_table
from tsheets_cli.resolve import resolve_jobcode, resolve_user

# Stderr console for messages that must not corrupt JSON output
err_console = Console(stderr=True)


def _get_current_user_id() -> int:
    """Get the current authenticated user's ID."""
    data = api_get("/current_user")
    users = data.get("results", {}).get("users", {})
    if not users:
        console.print("[bold red]Could not determine current user.[/]")
        raise typer.Exit(1)
    return int(next(iter(users.keys())))


def clock_in(
    jobcode: str = typer.Option(..., "--jobcode", help="Jobcode name or ID to clock in to"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes for this clock-in"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Start an active timer (clock in).

    Creates a new timesheet entry with a start time and no end time,
    which TSheets treats as an active/running timer. If you already
    have an active timer, it will be stopped first automatically.

    [dim]Examples:
      tsheets clock-in --jobcode "Admin"
      tsheets clock-in --jobcode "Project X" --notes "Morning standup"[/]
    """
    user_id = _get_current_user_id()
    jobcode_id = resolve_jobcode(jobcode)

    # Check for existing active timer and stop it first
    today = datetime.now().strftime("%Y-%m-%d")
    existing = api_get("/timesheets", params={
        "user_ids": str(user_id),
        "start_date": today,
        "end_date": today,
        "on_the_clock": "yes",
    })
    active_timesheets = existing.get("results", {}).get("timesheets", {})
    if active_timesheets:
        # Stop existing timer before starting a new one
        old_tid, old_ts = next(iter(active_timesheets.items()))
        now_stop = datetime.now(timezone.utc).isoformat()
        api_put("/timesheets", {"data": [{"id": int(old_tid), "end": now_stop}]})
        if not json_output:
            duration = old_ts.get("duration", 0)
            console.print(
                f"[yellow]Stopped existing timer (ID: {old_tid}, "
                f"duration: {format_duration(duration)}).[/]"
            )

    now = datetime.now(timezone.utc).isoformat()

    entry: dict = {
        "user_id": user_id,
        "type": "regular",
        "jobcode_id": jobcode_id,
        "start": now,
        "end": "",
    }
    if notes:
        entry["notes"] = notes

    data = api_post("/timesheets", {"data": [entry]})

    if json_output:
        print_json(data)
        return

    timesheets = data.get("results", {}).get("timesheets", {})
    if not timesheets:
        console.print("[bold red]Failed to create timer. Check API response.[/]")
        raise typer.Exit(1)

    for tid, ts in timesheets.items():
        status = ts.get("_status_extra", "")
        console.print(f"[green bold]Clocked in![/] Timer ID: {tid}")
        console.print(f"[dim]Jobcode: {jobcode} | Started at: {now}[/]")
        if ts.get("on_the_clock"):
            console.print("[green]Timer is now running.[/]")
        if status:
            console.print(f"[dim]{status}[/]")


def clock_out(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Stop the active timer (clock out).

    Finds any running timer for the current user and stops it by
    setting the end time to now. Shows the total duration of the
    completed entry.

    [dim]Example:  tsheets clock-out[/]
    """
    user_id = _get_current_user_id()

    # Find active timesheet (on_the_clock)
    today = datetime.now().strftime("%Y-%m-%d")
    data = api_get("/timesheets", params={
        "user_ids": str(user_id),
        "start_date": today,
        "end_date": today,
        "on_the_clock": "yes",
    })

    timesheets = data.get("results", {}).get("timesheets", {})
    if not timesheets:
        if json_output:
            print_json({"error": "No active timer found", "on_the_clock": False})
        else:
            console.print("[yellow]No active timer found. You are not clocked in.[/]")
            console.print("[dim]Use 'tsheets clock-in --jobcode <name>' to start a timer.[/]")
        raise typer.Exit(0)

    # Stop the first active timesheet
    tid, ts = next(iter(timesheets.items()))
    now = datetime.now(timezone.utc).isoformat()

    # Calculate elapsed time for display (since API duration may be 0 for active timers)
    start_str = ts.get("start", "")
    elapsed = 0
    try:
        start_dt = datetime.fromisoformat(start_str)
        elapsed = int((datetime.now(timezone.utc) - start_dt.astimezone(timezone.utc)).total_seconds())
    except (ValueError, TypeError):
        pass

    update_data = {
        "data": [{
            "id": int(tid),
            "end": now,
        }]
    }

    result = api_put("/timesheets", update_data)

    if json_output:
        print_json(result)
        return

    updated = result.get("results", {}).get("timesheets", {})
    if updated:
        for ut_id, ut in updated.items():
            duration = ut.get("duration", 0)
            # Use calculated elapsed if API returns 0
            if duration == 0 and elapsed > 0:
                duration = elapsed
            # Resolve jobcode name from supplemental data
            jc_id = str(ut.get("jobcode_id", ""))
            supp = result.get("supplemental_data", {}).get("jobcodes", {})
            jc_name = supp.get(jc_id, {}).get("name", jc_id)

            console.print(f"[green bold]Clocked out![/] Timer ID: {ut_id}")
            console.print(f"[dim]Jobcode: {jc_name} | Duration: {format_duration(duration)}[/]")
    else:
        console.print(f"[green bold]Clocked out![/] Timer ID: {tid}")
        console.print(f"[dim]Approximate duration: {format_duration(elapsed)}[/]")


def today(
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID (default: current user)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show hours worked today.

    Lists all time entries for the current day with jobcode, start/end
    times, and duration. Shows a running total at the bottom.

    [dim]Examples:
      tsheets today
      tsheets today --user "Jane Smith"[/]
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    params: dict = {
        "start_date": today_str,
        "end_date": today_str,
    }
    if user:
        params["user_ids"] = str(resolve_user(user))
    else:
        params["user_ids"] = str(_get_current_user_id())

    data = api_get("/timesheets", params=params)

    if json_output:
        print_json(data)
        return

    timesheets = data.get("results", {}).get("timesheets", {})
    supplemental = data.get("supplemental_data", {})
    jobcodes_supp = supplemental.get("jobcodes", {})

    total_seconds = 0
    rows = []
    for tid, ts in timesheets.items():
        jc_id = str(ts.get("jobcode_id", ""))
        jc_info = jobcodes_supp.get(jc_id, {})
        jc_name = jc_info.get("name", jc_id)
        duration = ts.get("duration", 0)
        on_clock = ts.get("on_the_clock", False)

        if on_clock:
            # Calculate elapsed time for active timer
            start_str = ts.get("start", "")
            try:
                start_dt = datetime.fromisoformat(start_str)
                elapsed = int((datetime.now(timezone.utc) - start_dt.astimezone(timezone.utc)).total_seconds())
                duration = elapsed
            except (ValueError, TypeError):
                pass

        total_seconds += duration

        status = "[green]Active[/]" if on_clock else format_duration(duration)
        rows.append([
            jc_name,
            ts.get("start", "").split("T")[1][:5] if "T" in ts.get("start", "") else "-",
            ts.get("end", "").split("T")[1][:5] if ts.get("end") and "T" in ts.get("end", "") else ("now" if on_clock else "-"),
            status,
            ts.get("notes", "") or "",
        ])

    print_table(
        f"Today ({today_str})",
        [
            ("Jobcode", "bold"),
            ("Start", ""),
            ("End", ""),
            ("Duration", "green"),
            ("Notes", "dim"),
        ],
        rows,
    )
    console.print(f"\n[bold]Total: {format_duration(total_seconds)}[/]")


def week(
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID (default: current user)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show hours worked this week (Monday through today).

    Displays a daily breakdown of hours from Monday to today with
    a weekly total. Great for a quick status check.

    [dim]Examples:
      tsheets week
      tsheets week --user "Jane Smith"[/]
    """
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    start_str = monday.strftime("%Y-%m-%d")
    end_str = now.strftime("%Y-%m-%d")

    params: dict = {
        "start_date": start_str,
        "end_date": end_str,
    }
    if user:
        params["user_ids"] = str(resolve_user(user))
    else:
        params["user_ids"] = str(_get_current_user_id())

    data = api_get("/timesheets", params=params)

    if json_output:
        print_json(data)
        return

    timesheets = data.get("results", {}).get("timesheets", {})
    supplemental = data.get("supplemental_data", {})
    jobcodes_supp = supplemental.get("jobcodes", {})

    # Group by day
    daily: dict[str, int] = {}
    total_seconds = 0
    for tid, ts in timesheets.items():
        date = ts.get("date", ts.get("start", "")[:10])
        duration = ts.get("duration", 0)
        on_clock = ts.get("on_the_clock", False)

        if on_clock:
            start_s = ts.get("start", "")
            try:
                start_dt = datetime.fromisoformat(start_s)
                duration = int((datetime.now(timezone.utc) - start_dt.astimezone(timezone.utc)).total_seconds())
            except (ValueError, TypeError):
                pass

        daily[date] = daily.get(date, 0) + duration
        total_seconds += duration

    rows = []
    for date in sorted(daily.keys()):
        day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
        rows.append([date, day_name, format_duration(daily[date])])

    print_table(
        f"This Week ({start_str} to {end_str})",
        [
            ("Date", ""),
            ("Day", "bold"),
            ("Hours", "green"),
        ],
        rows,
    )
    console.print(f"\n[bold]Week Total: {format_duration(total_seconds)}[/]")


def locate(
    user: str = typer.Option(..., "--user", "-u", help="User name or ID to locate"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date to check (YYYY-MM-DD, default: today)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show the last known GPS location for a user.

    Quick shortcut for finding where someone was/is. Searches back up to
    7 days if no data found on the target date.

    Examples:
        tsheets locate --user "Jane Smith"
        tsheets locate --user "Jane Smith" --date 2026-03-01
    """
    from tsheets_cli.output import format_date

    user_id = resolve_user(user)
    target_date = date or datetime.now().strftime("%Y-%m-%d")

    # Look back up to 7 days from target date to find data
    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    geos: dict = {}
    last_data: dict = {}
    for lookback in range(8):
        check_date = target_dt - timedelta(days=lookback)
        start_str = check_date.strftime("%Y-%m-%d")

        params: dict = {
            "user_ids": str(user_id),
            "start_date": start_str,
            "end_date": target_date,
        }
        last_data = api_get("/geolocations", params=params)
        geos = last_data.get("results", {}).get("geolocations", {})
        if geos:
            break

    if json_output:
        print_json(last_data)
        return

    if not geos:
        console.print(f"[dim]No geolocation data found for user {user_id} within 7 days of {target_date}.[/]")
        return

    # Find the most recent point
    _latest_id, latest = max(
        geos.items(),
        key=lambda x: x[1].get("created", ""),
    )

    lat = latest.get("latitude", "")
    lon = latest.get("longitude", "")
    accuracy = latest.get("accuracy")
    created = latest.get("created", "")

    accuracy_str = f" (accuracy: {accuracy}m)" if accuracy is not None else ""

    console.print(f"[bold]Last known location for user {user_id}:[/]")
    console.print(f"  Coordinates: [cyan]{lat}, {lon}[/]{accuracy_str}")
    console.print(f"  Timestamp:   {format_date(created)}")
    if lat and lon:
        console.print(f"  [dim]Google Maps:[/] https://www.google.com/maps?q={lat},{lon}")


def whosin(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show who is currently clocked in.

    Lists all employees with an active timer, including their current
    jobcode and shift duration.

    [dim]Example:  tsheets whosin[/]
    """
    data = api_post("/reports/current_totals", {"data": {}})

    if json_output:
        print_json(data)
        return

    totals = data.get("results", {}).get("current_totals", {})
    supplemental = data.get("supplemental_data", {})
    users_supp = supplemental.get("users", {})
    jobcodes_supp = supplemental.get("jobcodes", {})

    rows = []
    for uid, entry in totals.items():
        if uid == "totals":
            continue
        if not entry.get("on_the_clock"):
            continue

        user_info = users_supp.get(str(uid), {})
        user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or str(uid)

        shift_seconds = entry.get("shift_seconds", 0)
        day_seconds = entry.get("day_seconds", 0)
        jobcode_id = str(entry.get("jobcode_id", ""))
        jc_name = jobcodes_supp.get(jobcode_id, {}).get("name", jobcode_id) if jobcode_id else "-"

        rows.append([
            user_name,
            jc_name,
            format_duration(shift_seconds),
            format_duration(day_seconds),
        ])

    if not rows:
        console.print("[dim]Nobody is currently clocked in.[/]")
        return

    print_table(
        "Currently Clocked In",
        [
            ("Name", "bold"),
            ("Jobcode", "cyan"),
            ("Shift Duration", "green"),
            ("Day Total", "green"),
        ],
        rows,
    )


def payroll(
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Start date (YYYY-MM-DD, default: start of last week)"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="End date (YYYY-MM-DD, default: end of last week)"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="User name or ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Quick payroll report (defaults to last complete week).

    Shortcut for 'tsheets reports payroll'. If no dates are specified,
    defaults to the most recently completed Mon-Sun week.

    Examples:
        tsheets payroll
        tsheets payroll --start 2026-02-24 --end 2026-03-02
        tsheets payroll --user "Jane Smith"
    """
    from tsheets_cli.commands.reports import payroll_report

    if not start or not end:
        now = datetime.now()
        # Find end of last week (most recent Sunday)
        days_since_sunday = (now.weekday() + 1) % 7
        if days_since_sunday == 0:
            days_since_sunday = 7  # If today is Sunday, use last Sunday
        last_sunday = now - timedelta(days=days_since_sunday)
        last_monday = last_sunday - timedelta(days=6)
        start = start or last_monday.strftime("%Y-%m-%d")
        end = end or last_sunday.strftime("%Y-%m-%d")

    payroll_report(start=start, end=end, user=user, json_output=json_output)
