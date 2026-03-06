"""Projects commands - list projects."""

from __future__ import annotations

from typing import Optional

import typer

from tsheets_cli.api import api_get
from tsheets_cli.output import print_json, print_table

app = typer.Typer(
    help="List and view project records.",
    rich_markup_mode="rich",
)


@app.command("list")
def list_projects(
    active: str = typer.Option("yes", help="Filter: yes, no, or both"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all projects.

    Shows project ID, name, description, and status.

    [dim]Examples:
      tsheets projects list
      tsheets projects list --active both --json[/]
    """
    params: dict = {"active": active}
    data = api_get("/projects", params=params)

    if json_output:
        print_json(data)
        return

    projects = data.get("results", {}).get("projects", {})
    rows = []
    for pid, proj in projects.items():
        rows.append([
            str(pid),
            proj.get("name", ""),
            proj.get("description", "") or "",
            proj.get("status", ""),
        ])

    print_table(
        "Projects",
        [
            ("ID", "cyan"),
            ("Name", "bold"),
            ("Description", ""),
            ("Status", "green"),
        ],
        rows,
    )
