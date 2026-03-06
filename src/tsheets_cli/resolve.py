"""Name-to-ID resolution for users, jobcodes, and projects."""

from __future__ import annotations

import sys
from typing import Any

from rich.console import Console

from tsheets_cli.api import api_get

console = Console(stderr=True)


def _is_numeric(value: str) -> bool:
    """Check if a string is a numeric ID."""
    try:
        int(value)
        return True
    except ValueError:
        return False


def resolve_user(name_or_id: str) -> int:
    """Resolve a user name (or numeric ID) to a user ID.

    Matches against first_name + last_name, case-insensitive.
    """
    if _is_numeric(name_or_id):
        return int(name_or_id)

    data = api_get("/users", params={"active": "both"})
    users = data.get("results", {}).get("users", {})

    search = name_or_id.strip().lower()
    matches: list[tuple[int, str]] = []

    for uid, user in users.items():
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        if full_name.lower() == search:
            return int(uid)
        if search in full_name.lower():
            matches.append((int(uid), full_name))

    if len(matches) == 1:
        return matches[0][0]
    elif len(matches) > 1:
        console.print(f"[yellow]Ambiguous user name '{name_or_id}'. Matches:[/]")
        for uid, name in matches:
            console.print(f"  {uid}: {name}")
        console.print("\n[yellow]Use the numeric ID or a more specific name.[/]")
        sys.exit(1)
    else:
        console.print(
            f"[bold red]User not found:[/] '{name_or_id}'\n"
            "[yellow]Run 'tsheets users list' to see available users.[/]"
        )
        sys.exit(1)


def _fetch_all_jobcodes(name_filter: str | None = None) -> dict[str, Any]:
    """Fetch all jobcodes, handling pagination.

    Args:
        name_filter: Optional name substring to pass as server-side filter.

    Returns:
        Merged dict of jobcode_id -> jobcode data across all pages.
    """
    all_jobcodes: dict[str, Any] = {}
    page = 1
    while True:
        params: dict[str, Any] = {"active": "both", "page": page}
        if name_filter:
            params["name"] = name_filter
        data = api_get("/jobcodes", params=params)
        jobcodes = data.get("results", {}).get("jobcodes", {})
        if not jobcodes:
            break
        all_jobcodes.update(jobcodes)
        # TSheets returns "more": true in supplemental_data or we check if we got a full page
        more = data.get("more", False)
        if not more:
            break
        page += 1
    return all_jobcodes


def resolve_jobcode(name_or_id: str) -> int:
    """Resolve a jobcode name (or partial name) to a jobcode ID.

    Accepts a numeric ID (returned as-is), an exact jobcode name, or a
    partial/substring match.  Queries the TSheets ``/jobcodes`` endpoint
    with server-side name filtering when possible, and handles pagination
    so no results are missed.

    Matching priority:
        1. Exact case-insensitive match → returned immediately.
        2. Single substring match → returned.
        3. Multiple substring matches → prints candidates and exits.
        4. No matches → prints error with guidance and exits.
    """
    if _is_numeric(name_or_id):
        return int(name_or_id)

    search = name_or_id.strip().lower()

    # Use server-side name filter to reduce payload when possible
    jobcodes = _fetch_all_jobcodes(name_filter=name_or_id.strip())

    # If server-side filter returned nothing, fall back to fetching all
    # (the TSheets name filter is exact-prefix, so partial matches may be missed)
    if not jobcodes:
        jobcodes = _fetch_all_jobcodes()

    exact_match: int | None = None
    matches: list[tuple[int, str]] = []

    for jid, jc in jobcodes.items():
        jc_name = jc.get("name", "")
        if jc_name.lower() == search:
            exact_match = int(jid)
        if search in jc_name.lower():
            matches.append((int(jid), jc_name))

    # Exact match always wins, even if there are other substring matches
    if exact_match is not None:
        return exact_match

    if len(matches) == 1:
        return matches[0][0]
    elif len(matches) > 1:
        console.print(f"[yellow]Ambiguous jobcode name '{name_or_id}'. Matches:[/]")
        for jid, name in matches:
            console.print(f"  {jid}: {name}")
        console.print("\n[yellow]Use the numeric ID or a more specific name.[/]")
        sys.exit(1)
    else:
        console.print(
            f"[bold red]Jobcode not found:[/] '{name_or_id}'\n"
            "[yellow]Run 'tsheets jobcodes list' to see available jobcodes.[/]"
        )
        sys.exit(1)


def resolve_project(name_or_id: str) -> int:
    """Resolve a project name (or numeric ID) to a project ID.

    Matches against project name, case-insensitive.
    """
    if _is_numeric(name_or_id):
        return int(name_or_id)

    data = api_get("/projects", params={"active": "both"})
    projects = data.get("results", {}).get("projects", {})

    search = name_or_id.strip().lower()
    matches: list[tuple[int, str]] = []

    for pid, proj in projects.items():
        proj_name = proj.get("name", "")
        if proj_name.lower() == search:
            return int(pid)
        if search in proj_name.lower():
            matches.append((int(pid), proj_name))

    if len(matches) == 1:
        return matches[0][0]
    elif len(matches) > 1:
        console.print(f"[yellow]Ambiguous project name '{name_or_id}'. Matches:[/]")
        for pid, name in matches:
            console.print(f"  {pid}: {name}")
        console.print("\n[yellow]Use the numeric ID or a more specific name.[/]")
        sys.exit(1)
    else:
        console.print(
            f"[bold red]Project not found:[/] '{name_or_id}'\n"
            "[yellow]Run 'tsheets projects list' to see available projects.[/]"
        )
        sys.exit(1)
