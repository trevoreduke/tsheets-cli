"""Jobcodes commands - list and create jobcodes (projects/tasks)."""

from __future__ import annotations

from typing import Optional

import typer

from tsheets_cli.api import api_get, api_post
from tsheets_cli.output import console, print_json, print_table
from tsheets_cli.resolve import resolve_jobcode

app = typer.Typer(
    help="List and create jobcodes (projects/tasks).",
    rich_markup_mode="rich",
)


@app.command("list")
def list_jobcodes(
    active: str = typer.Option("yes", help="Filter: yes, no, or both"),
    limit: Optional[int] = typer.Option(None, help="Max results to return"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all jobcodes (projects and tasks).

    Shows jobcode ID, name, parent, billable status, and short code.

    [dim]Examples:
      tsheets jobcodes list
      tsheets jobcodes list --active both
      tsheets jobcodes list --json[/]
    """
    params: dict = {"active": active}
    if limit:
        params["limit"] = limit

    data = api_get("/jobcodes", params=params)

    if json_output:
        print_json(data)
        return

    jobcodes = data.get("results", {}).get("jobcodes", {})
    rows = []
    for jid, jc in jobcodes.items():
        rows.append([
            str(jid),
            jc.get("name", ""),
            str(jc.get("parent_id", 0)),
            "Yes" if jc.get("billable") else "No",
            jc.get("short_code", "") or "",
            "Active" if jc.get("active") else "Inactive",
        ])

    print_table(
        "Jobcodes",
        [
            ("ID", "cyan"),
            ("Name", "bold"),
            ("Parent ID", "dim"),
            ("Billable", ""),
            ("Short Code", ""),
            ("Status", "green"),
        ],
        rows,
    )


@app.command("create")
def create_jobcode(
    name: str = typer.Option(..., "--name", help="Jobcode name"),
    parent_id: Optional[str] = typer.Option(None, "--parent", "--parent-id", help="Parent jobcode name or ID (omit for top-level)"),
    billable: bool = typer.Option(True, "--billable/--no-billable", help="Whether billable"),
    assigned_to_all: bool = typer.Option(True, "--assigned-to-all/--not-assigned-to-all", help="Assign to all users"),
    short_code: Optional[str] = typer.Option(None, "--short-code", help="Short code abbreviation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a new jobcode (project/task).

    Creates a new jobcode at the top level or nested under a parent.
    Parent can be specified by name or numeric ID.

    [dim]Examples:
      tsheets jobcodes create --name "New Project"
      tsheets jobcodes create --name "Subtask" --parent "New Project" --no-billable
      tsheets jobcodes create --name "Quick Job" --short-code QJ[/]
    """
    jobcode: dict = {
        "name": name,
        "billable": billable,
        "assigned_to_all": assigned_to_all,
    }
    if parent_id:
        jobcode["parent_id"] = resolve_jobcode(parent_id)
    if short_code:
        jobcode["short_code"] = short_code

    data = api_post("/jobcodes", {"data": [jobcode]})

    if json_output:
        print_json(data)
        return

    jobcodes = data.get("results", {}).get("jobcodes", {})
    for jid, jc in jobcodes.items():
        console.print(f"[green]Jobcode created:[/] {jc.get('name', '')} (ID: {jid})")
