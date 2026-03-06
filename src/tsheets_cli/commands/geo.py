"""Geolocation commands - view GPS data and geofence configs."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import typer

from tsheets_cli.api import api_get
from tsheets_cli.output import console, format_date, print_json, print_table
from tsheets_cli.resolve import resolve_user

app = typer.Typer(
    help="GPS geolocation data and tracking.",
    rich_markup_mode="rich",
)


def _fetch_all_geolocations(params: dict) -> list[dict]:
    """Fetch geolocations with pagination support.

    The TSheets /geolocations endpoint returns up to 200 results per page
    and uses 'more' flag + page param for pagination.
    """
    all_geos: list[dict] = []
    page = 1

    while True:
        params["page"] = page
        data = api_get("/geolocations", params=params)
        geos = data.get("results", {}).get("geolocations", {})

        for gid, geo in geos.items():
            geo["_id"] = gid
            all_geos.append(geo)

        # Check if more pages exist
        if data.get("more", False):
            page += 1
        else:
            break

    return all_geos


@app.command("list")
def list_geolocations(
    user: str = typer.Option(..., "--user", "-u", help="User name or ID"),
    start: str = typer.Option(..., "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", "-e", help="End date (YYYY-MM-DD)"),
    page: int = typer.Option(1, "--page", "-p", help="Page number for paginated results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List GPS geolocations for a user within a date range.

    Shows timestamped latitude/longitude points recorded by the TSheets
    mobile app while the user was clocked in.

    Examples:
        tsheets geo list --user "Jane Smith" --start 2026-03-01 --end 2026-03-06
        tsheets geo list --user 12345 --start 2026-03-01 --end 2026-03-01 --json
    """
    user_id = resolve_user(user)
    params: dict = {
        "user_ids": str(user_id),
        "start_date": start,
        "end_date": end,
        "page": page,
    }

    data = api_get("/geolocations", params=params)

    if json_output:
        print_json(data)
        return

    geos = data.get("results", {}).get("geolocations", {})
    rows = []
    for gid, geo in geos.items():
        lat = geo.get("latitude", "")
        lon = geo.get("longitude", "")
        accuracy = geo.get("accuracy")
        altitude = geo.get("altitude")
        speed = geo.get("speed")
        heading = geo.get("heading")
        source = geo.get("source", "")
        created = geo.get("created", "")

        # Format optional numeric fields
        accuracy_str = f"{accuracy}m" if accuracy is not None else "-"
        altitude_str = f"{altitude}m" if altitude is not None else "-"
        speed_str = f"{speed} m/s" if speed is not None else "-"

        rows.append([
            str(gid),
            f"{lat}, {lon}" if lat and lon else "-",
            accuracy_str,
            altitude_str,
            speed_str,
            format_date(created),
            source or "-",
        ])

    has_more = data.get("more", False)

    print_table(
        f"Geolocations (User {user_id})",
        [
            ("ID", "cyan"),
            ("Coordinates", "bold"),
            ("Accuracy", "dim"),
            ("Altitude", "dim"),
            ("Speed", ""),
            ("Timestamp", ""),
            ("Source", "dim"),
        ],
        rows,
    )

    if has_more:
        console.print(f"\n[yellow]More results available.[/] Use --page {page + 1} to see next page.")


@app.command("latest")
def latest_geolocations(
    user: str = typer.Option(..., "--user", "-u", help="User name or ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent points to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show the most recent GPS points for a user.

    Fetches the last N geolocation records from today, or extends backward
    if no results found today.

    Examples:
        tsheets geo latest --user "Jane Smith"
        tsheets geo latest --user "Jane Smith" --limit 5
    """
    user_id = resolve_user(user)

    # Start with today, look back up to 7 days if no results
    today = datetime.now()
    last_data: dict = {}
    geos: dict = {}
    for lookback in range(8):
        check_date = today - timedelta(days=lookback)
        start_str = check_date.strftime("%Y-%m-%d")
        end_str = today.strftime("%Y-%m-%d")

        params: dict = {
            "user_ids": str(user_id),
            "start_date": start_str,
            "end_date": end_str,
        }

        last_data = api_get("/geolocations", params=params)
        geos = last_data.get("results", {}).get("geolocations", {})
        if geos:
            break

    if json_output:
        print_json(last_data)
        return

    if not geos:
        console.print(f"[dim]No geolocation data found for user {user_id} in the past 7 days.[/]")
        return

    # Sort by created timestamp (most recent first) and take limit
    sorted_geos = sorted(
        geos.items(),
        key=lambda x: x[1].get("created", ""),
        reverse=True,
    )[:limit]

    rows = []
    for gid, geo in sorted_geos:
        lat = geo.get("latitude", "")
        lon = geo.get("longitude", "")
        accuracy = geo.get("accuracy")
        created = geo.get("created", "")

        accuracy_str = f"{accuracy}m" if accuracy is not None else "-"

        rows.append([
            f"{lat}, {lon}" if lat and lon else "-",
            accuracy_str,
            format_date(created),
        ])

    print_table(
        f"Latest Geolocations (User {user_id})",
        [
            ("Coordinates", "bold"),
            ("Accuracy", "dim"),
            ("Timestamp", ""),
        ],
        rows,
    )

    if sorted_geos:
        latest = sorted_geos[0][1]
        lat = latest.get("latitude", "")
        lon = latest.get("longitude", "")
        if lat and lon:
            console.print(
                f"\n[dim]Google Maps:[/] https://www.google.com/maps?q={lat},{lon}"
            )


# ── Geofences ─────────────────────────────────────────────────────────

geofences_app = typer.Typer(
    help="Geofence boundary configurations.",
    rich_markup_mode="rich",
)


@geofences_app.command("list")
def list_geofences(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all geofence configurations.

    Shows configured geofence boundaries including center coordinates,
    radius, and enabled status.

    Examples:
        tsheets geofences list
        tsheets geofences list --json
    """
    data = api_get("/geofence_configs")

    if json_output:
        print_json(data)
        return

    configs = data.get("results", {}).get("geofence_configs", {})
    rows = []
    for gid, gf in configs.items():
        lat = gf.get("latitude", "")
        lon = gf.get("longitude", "")
        radius = gf.get("radius", "")

        rows.append([
            str(gid),
            gf.get("type_name", gf.get("type", "")),
            f"{lat}, {lon}" if lat and lon else "-",
            f"{radius}m" if radius else "-",
            "[green]Yes[/]" if gf.get("enabled") else "[red]No[/]",
        ])

    print_table(
        "Geofence Configurations",
        [
            ("ID", "cyan"),
            ("Name", "bold"),
            ("Center", ""),
            ("Radius", ""),
            ("Enabled", ""),
        ],
        rows,
    )
