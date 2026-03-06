"""Reports commands - payroll, current totals, current all, project estimates, project details."""

from __future__ import annotations

from typing import Optional

import typer

from tsheets_cli.api import api_get
from tsheets_cli.output import console, format_duration, print_json, print_table
from tsheets_cli.resolve import resolve_project, resolve_user

app = typer.Typer(
    help="Payroll, current totals, and project reports.",
    rich_markup_mode="rich",
)


def _extract_payroll_seconds(entry: dict | list) -> dict[str, int]:
    """Extract payroll seconds from an entry, handling both dict and list formats.

    The TSheets API returns payroll entries as a list of dicts per user,
    where each dict represents a pay period. This function aggregates
    all periods into a single totals dict.
    """
    totals = {
        "total_re_seconds": 0,
        "total_ot_seconds": 0,
        "total_dt_seconds": 0,
        "total_pto_seconds": 0,
        "total_work_seconds": 0,
    }

    if isinstance(entry, list):
        # API returns array of pay period entries per user
        for period in entry:
            if isinstance(period, dict):
                for key in totals:
                    totals[key] += period.get(key, 0)
    elif isinstance(entry, dict):
        # Fallback: single dict entry
        for key in totals:
            totals[key] = entry.get(key, 0)

    # Calculate total work if not provided by the API
    if totals["total_work_seconds"] == 0:
        totals["total_work_seconds"] = (
            totals["total_re_seconds"]
            + totals["total_ot_seconds"]
            + totals["total_dt_seconds"]
        )

    return totals


@app.command("payroll")
def payroll_report(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get payroll report for a date range.

    Shows regular, overtime, double-time, and PTO hours for each employee.
    Includes a grand total row when multiple employees are shown.
    Employees with zero hours are omitted from the output.

    Examples:
        tsheets reports payroll --start 2026-02-24 --end 2026-03-02
        tsheets reports payroll --start 2026-02-24 --end 2026-03-02 --user "Jane Smith"
    """
    params: dict = {"start_date": start, "end_date": end}
    if user:
        params["user_ids"] = str(resolve_user(user))

    data = api_get("/reports/payroll", params=params)

    if json_output:
        print_json(data)
        return

    payroll = data.get("results", {}).get("payroll_report", {})
    supplemental = data.get("supplemental_data", {})
    users_supp = supplemental.get("users", {})

    if not payroll:
        console.print(f"[dim]No payroll data found for {start} to {end}.[/]")
        return

    rows = []
    grand_totals = {
        "total_re_seconds": 0,
        "total_ot_seconds": 0,
        "total_dt_seconds": 0,
        "total_pto_seconds": 0,
        "total_work_seconds": 0,
    }

    for uid, entry in payroll.items():
        user_info = users_supp.get(str(uid), {})
        user_name = (
            f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            or str(uid)
        )

        totals = _extract_payroll_seconds(entry)

        # Skip users with zero hours
        if totals["total_work_seconds"] == 0 and totals["total_pto_seconds"] == 0:
            continue

        # Accumulate grand totals
        for key in grand_totals:
            grand_totals[key] += totals[key]

        rows.append([
            user_name,
            format_duration(totals["total_re_seconds"]),
            format_duration(totals["total_ot_seconds"]),
            format_duration(totals["total_dt_seconds"]),
            format_duration(totals["total_pto_seconds"]),
            format_duration(totals["total_work_seconds"]),
        ])

    # Sort rows by employee name
    rows.sort(key=lambda r: r[0].lower())

    # Add grand total row if multiple employees
    if len(rows) > 1:
        rows.append([
            "[bold]TOTAL[/]",
            f"[bold]{format_duration(grand_totals['total_re_seconds'])}[/]",
            f"[bold]{format_duration(grand_totals['total_ot_seconds'])}[/]",
            f"[bold]{format_duration(grand_totals['total_dt_seconds'])}[/]",
            f"[bold]{format_duration(grand_totals['total_pto_seconds'])}[/]",
            f"[bold]{format_duration(grand_totals['total_work_seconds'])}[/]",
        ])

    print_table(
        f"Payroll Report ({start} to {end})",
        [
            ("Employee", "bold"),
            ("Regular", "green"),
            ("Overtime", "yellow"),
            ("Double Time", "red"),
            ("PTO", "blue"),
            ("Total", "cyan"),
        ],
        rows,
    )


@app.command("totals")
def current_totals(
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID"),
    on_the_clock: bool = typer.Option(False, "--on-the-clock", help="Show only users currently clocked in"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get current period totals (hours worked this pay period).

    Shows regular, overtime, double-time, and PTO hours for each user in
    the current pay period. Also displays shift duration and today's hours
    for users who are currently clocked in.

    Examples:
        tsheets reports totals
        tsheets reports totals --user "Jane Smith"
        tsheets reports totals --on-the-clock
    """
    params: dict = {}
    if user:
        params["user_ids"] = str(resolve_user(user))

    data = api_get("/reports/current_totals", params=params)

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

        # Apply on-the-clock filter if requested
        is_on_clock = entry.get("on_the_clock", False)
        if on_the_clock and not is_on_clock:
            continue

        user_info = users_supp.get(str(uid), {})
        user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or str(uid)

        # Build clock status with jobcode name and shift duration for active users
        clock_status = "No"
        if is_on_clock:
            jc_id = str(entry.get("jobcode_id", ""))
            jc_info = jobcodes_supp.get(jc_id, {})
            jc_name = jc_info.get("name", jc_id) if jc_id else ""
            shift_dur = format_duration(entry.get("shift_seconds", 0))
            if jc_name:
                clock_status = f"[green]{jc_name}[/] ({shift_dur})"
            else:
                clock_status = f"[green]Yes[/] ({shift_dur})"

        rows.append([
            user_name,
            format_duration(entry.get("total_re_seconds", 0)),
            format_duration(entry.get("total_ot_seconds", 0)),
            format_duration(entry.get("total_dt_seconds", 0)),
            format_duration(entry.get("total_pto_seconds", 0)),
            format_duration(entry.get("day_seconds", 0)),
            clock_status,
        ])

    print_table(
        "Current Period Totals",
        [
            ("Name", "bold"),
            ("Regular", "green"),
            ("Overtime", "yellow"),
            ("Double Time", "red"),
            ("PTO", "blue"),
            ("Today", "cyan"),
            ("On Clock", ""),
        ],
        rows,
    )

    # Print aggregate totals summary when showing multiple users
    agg = totals.get("totals", {})
    if agg and not user and rows:
        console.print(
            f"\n[bold]Period Totals:[/] "
            f"Regular: [green]{format_duration(agg.get('total_re_seconds', 0))}[/] | "
            f"OT: [yellow]{format_duration(agg.get('total_ot_seconds', 0))}[/] | "
            f"DT: [red]{format_duration(agg.get('total_dt_seconds', 0))}[/] | "
            f"PTO: [blue]{format_duration(agg.get('total_pto_seconds', 0))}[/]"
        )


@app.command("project-estimate")
def project_estimate(
    project: Optional[str] = typer.Option(None, "--project", help="Project name or ID (omit for all)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get project estimate vs actual hours.

    Shows estimated time vs actual time spent on projects.
    Omit --project to see all projects.

    Examples:
        tsheets reports project-estimate
        tsheets reports project-estimate --project "Website Redesign"
    """
    params: dict = {}
    if project:
        project_id = resolve_project(project)
        params["project_ids"] = str(project_id)

    data = api_get("/reports/project_estimate", params=params)

    if json_output:
        print_json(data)
        return

    estimates = data.get("results", {}).get("project_estimate_report", {})
    supplemental = data.get("supplemental_data", {})
    projects_supp = supplemental.get("projects", {})

    rows = []
    for pid, entry in estimates.items():
        proj_info = projects_supp.get(str(pid), {})
        proj_name = proj_info.get("name", entry.get("project_name", str(pid)))
        estimated = entry.get("estimated_seconds", 0) or 0
        actual = entry.get("actual_seconds", 0) or 0

        # Calculate percent from seconds if not provided
        pct = entry.get("percent_complete")
        if pct is None and estimated > 0:
            pct = (actual / estimated) * 100
        elif pct is None:
            pct = 0.0

        rows.append([
            str(pid),
            proj_name,
            format_duration(estimated),
            format_duration(actual),
            f"{pct:.0f}%",
        ])

    print_table(
        "Project Estimate vs Actual",
        [
            ("Project ID", "cyan"),
            ("Project", "bold"),
            ("Estimated", "blue"),
            ("Actual", "green"),
            ("% Complete", "yellow"),
        ],
        rows,
    )


@app.command("current-all")
def current_all(
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get current timesheets for all users (who's on the clock with details).

    Shows every user's current clock status including their active jobcode,
    shift duration, day total, and pay period totals. More detailed than
    'totals' — includes the actual timesheet entry data.
    """
    params: dict = {}
    if user:
        params["user_ids"] = str(resolve_user(user))

    data = api_get("/reports/current_all", params=params)

    if json_output:
        print_json(data)
        return

    current_all_data = data.get("results", {}).get("current_all", {})
    supplemental = data.get("supplemental_data", {})
    users_supp = supplemental.get("users", {})
    jobcodes_supp = supplemental.get("jobcodes", {})

    rows = []
    for uid, entry in current_all_data.items():
        if uid in ("totals",):
            continue

        user_info = users_supp.get(str(uid), {})
        user_name = (
            f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            or str(uid)
        )

        on_clock = entry.get("on_the_clock", False)
        status = "[green]On Clock[/]" if on_clock else "[dim]Off[/]"

        # Resolve jobcode name from supplemental data
        jc_id = str(entry.get("jobcode_id", ""))
        jc_name = jobcodes_supp.get(jc_id, {}).get("name", jc_id) if jc_id else "-"

        shift_secs = entry.get("shift_seconds", 0)
        day_secs = entry.get("day_seconds", 0)
        total_re = entry.get("total_re_seconds", 0)
        total_ot = entry.get("total_ot_seconds", 0)
        total_pto = entry.get("total_pto_seconds", 0)

        rows.append([
            user_name,
            status,
            jc_name,
            format_duration(shift_secs),
            format_duration(day_secs),
            format_duration(total_re),
            format_duration(total_ot),
            format_duration(total_pto),
        ])

    # Sort: on-clock users first, then alphabetically
    rows.sort(key=lambda r: (0 if "On Clock" in r[1] else 1, r[0]))

    print_table(
        "Current All — Detailed Clock Status",
        [
            ("Name", "bold"),
            ("Status", ""),
            ("Jobcode", "cyan"),
            ("Shift", "green"),
            ("Day Total", "green"),
            ("Regular", "green"),
            ("Overtime", "yellow"),
            ("PTO", "blue"),
        ],
        rows,
    )


@app.command("project")
def project_report(
    project: Optional[str] = typer.Option(None, "--project", help="Project name or ID (omit for all)"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    user: Optional[str] = typer.Option(None, "--user", help="User name or ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get project time report with per-user and per-jobcode breakdowns.

    Shows total hours spent on projects, broken down by user and jobcode.
    The TSheets project report returns a nested structure:
    project -> user -> jobcode -> time totals.

    Examples:
        tsheets reports project --start 2026-01-01 --end 2026-01-31
        tsheets reports project --project "Office Build-Out" --start 2026-02-01 --end 2026-02-28
        tsheets reports project --user "Jane Smith" --start 2026-03-01 --end 2026-03-06
    """
    params: dict = {}
    if project:
        project_id = resolve_project(project)
        params["project_ids"] = str(project_id)
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    if user:
        params["user_ids"] = str(resolve_user(user))

    data = api_get("/reports/project", params=params)

    if json_output:
        print_json(data)
        return

    report = data.get("results", {}).get("project_report", {})
    supplemental = data.get("supplemental_data", {})
    users_supp = supplemental.get("users", {})
    jobcodes_supp = supplemental.get("jobcodes", {})
    projects_supp = supplemental.get("projects", {})

    filters = report.get("filters", {})
    start_date = filters.get("start_date", start or "?")
    end_date = filters.get("end_date", end or "?")

    rows = []
    grand_total_secs = 0

    # The project report structure can vary:
    # Layout A: totals_report = { project_id: { user_id: { jobcode_id: { seconds... } } } }
    # Layout B: by_user = { user_id: { total_re_seconds, ... } }
    # Layout C: flat totals dict
    totals_report = report.get("totals_report", {})

    if totals_report and isinstance(totals_report, dict):
        # Nested project -> user -> jobcode structure
        for pid, user_data in totals_report.items():
            proj_info = projects_supp.get(str(pid), {})
            proj_name = proj_info.get("name", str(pid))

            if not isinstance(user_data, dict):
                continue

            for uid, jobcode_data in user_data.items():
                user_info = users_supp.get(str(uid), {})
                user_name = (
                    f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                    or str(uid)
                )

                if not isinstance(jobcode_data, dict):
                    continue

                # Check if this level has time fields directly (user-level totals)
                if "total_re_seconds" in jobcode_data or "total_work_seconds" in jobcode_data:
                    re_secs = jobcode_data.get("total_re_seconds", 0) or 0
                    ot_secs = jobcode_data.get("total_ot_seconds", 0) or 0
                    dt_secs = jobcode_data.get("total_dt_seconds", 0) or 0
                    work_secs = jobcode_data.get("total_work_seconds", 0) or 0
                    total = work_secs if work_secs else re_secs + ot_secs + dt_secs
                    grand_total_secs += total

                    rows.append([
                        proj_name,
                        user_name,
                        "-",
                        format_duration(re_secs),
                        format_duration(ot_secs),
                        format_duration(total),
                    ])
                else:
                    # Nested jobcode level: user_data -> jobcode_id -> time_data
                    for jid, time_data in jobcode_data.items():
                        if not isinstance(time_data, dict):
                            continue
                        jc_info = jobcodes_supp.get(str(jid), {})
                        jc_name = jc_info.get("name", str(jid))

                        re_secs = time_data.get("total_re_seconds", 0) or 0
                        ot_secs = time_data.get("total_ot_seconds", 0) or 0
                        dt_secs = time_data.get("total_dt_seconds", 0) or 0
                        work_secs = time_data.get("total_work_seconds", 0) or 0
                        total = work_secs if work_secs else re_secs + ot_secs + dt_secs
                        grand_total_secs += total

                        rows.append([
                            proj_name,
                            user_name,
                            jc_name,
                            format_duration(re_secs),
                            format_duration(ot_secs),
                            format_duration(total),
                        ])
    else:
        # Fallback: try flat or by_user structures
        by_user = report.get("by_user", {})
        totals = report.get("totals", {})

        source = by_user if isinstance(by_user, dict) and by_user else totals
        if isinstance(source, dict):
            for uid, entry in source.items():
                if not isinstance(entry, dict):
                    continue
                user_info = users_supp.get(str(uid), {})
                user_name = (
                    f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                    or str(uid)
                )
                re_secs = entry.get("total_re_seconds", 0) or 0
                ot_secs = entry.get("total_ot_seconds", 0) or 0
                work_secs = entry.get("total_work_seconds", entry.get("total_seconds", 0)) or 0
                total = work_secs if work_secs else re_secs + ot_secs
                grand_total_secs += total

                rows.append([
                    project or "All",
                    user_name,
                    "-",
                    format_duration(re_secs),
                    format_duration(ot_secs),
                    format_duration(total),
                ])

    title = "Project Report"
    if start_date != "?" or end_date != "?":
        title = f"Project Report ({start_date} to {end_date})"

    print_table(
        title,
        [
            ("Project", "bold"),
            ("User", ""),
            ("Jobcode", "dim"),
            ("Regular", "green"),
            ("Overtime", "yellow"),
            ("Total", "cyan bold"),
        ],
        rows,
    )

    # Print grand total if there are multiple rows
    if len(rows) > 1 and grand_total_secs > 0:
        console.print(f"\n[bold]Grand Total:[/] [cyan]{format_duration(grand_total_secs)}[/]")
