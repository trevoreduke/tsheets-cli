"""Users commands - list users in the organization."""

from __future__ import annotations

from typing import Optional

import typer

from tsheets_cli.api import api_get
from tsheets_cli.output import console, print_json, print_table

app = typer.Typer(
    help="List and manage users in the organization.",
    rich_markup_mode="rich",
)


@app.command("list")
def list_users(
    active: str = typer.Option("yes", help="Filter: yes, no, or both"),
    limit: Optional[int] = typer.Option(None, help="Max results to return"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all users in the organization.

    Shows user ID, name, email, group, and active status. Use --active to
    filter by status.

    [dim]Examples:
      tsheets users list
      tsheets users list --active both
      tsheets users list --limit 10 --json[/]
    """
    params: dict = {"active": active}
    if limit:
        params["limit"] = limit

    data = api_get("/users", params=params)

    if json_output:
        print_json(data)
        return

    users = data.get("results", {}).get("users", {})
    rows = []
    for uid, user in users.items():
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        rows.append([
            str(uid),
            full_name,
            user.get("email", "-"),
            str(user.get("group_id", 0) or "-"),
            "Active" if user.get("active") else "Inactive",
        ])

    print_table(
        "Users",
        [
            ("ID", "cyan"),
            ("Name", "bold"),
            ("Email", ""),
            ("Group ID", "dim"),
            ("Status", "green"),
        ],
        rows,
    )
