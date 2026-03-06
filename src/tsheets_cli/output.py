"""Output formatting: Rich tables for humans, JSON for machines, CSV for spreadsheets."""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def print_json(data: Any) -> None:
    """Print data as formatted, valid JSON to stdout.

    Uses plain sys.stdout (not Rich console) to guarantee clean JSON
    output with no ANSI escape codes, even when stdout is a terminal.
    This ensures `tsheets ... --json | jq .` always works.
    """
    sys.stdout.write(json.dumps(data, indent=2, default=str) + "\n")
    sys.stdout.flush()


def print_table(
    title: str,
    columns: list[tuple[str, str]],
    rows: list[list[str]],
) -> None:
    """Print a Rich table.

    Args:
        title: Table title
        columns: List of (header, style) tuples
        rows: List of row data (list of strings)
    """
    if not rows:
        console.print(f"[dim]No results found for {title}.[/]")
        return

    table = Table(title=title, show_lines=False)
    for header, style in columns:
        table.add_column(header, style=style)

    for row in rows:
        table.add_row(*row)

    console.print(table)


def _strip_rich_markup(text: str) -> str:
    """Remove Rich markup tags like [bold], [green], [/], etc."""
    return re.sub(r"\[/?[^\]]*\]", "", text)


def print_csv(
    columns: list[tuple[str, str]],
    rows: list[list[str]],
    file: str | None = None,
) -> None:
    """Print data as CSV to stdout or a file.

    Strips Rich markup from cell values so the CSV is clean.

    Args:
        columns: List of (header, style) tuples
        rows: List of row data (list of strings)
        file: Optional file path to write to (prints to stdout if None)
    """
    headers = [h for h, _ in columns]
    clean_rows = [[_strip_rich_markup(cell) for cell in row] for row in rows]

    if file:
        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(clean_rows)
        Console(stderr=True).print(f"[green]Wrote {len(clean_rows)} rows to {file}[/]")
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(clean_rows)
        sys.stdout.write(buf.getvalue())
        sys.stdout.flush()


def format_duration(seconds: int | None) -> str:
    """Format seconds into HH:MM:SS or h m format."""
    if seconds is None or seconds == 0:
        return "0:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def format_date(dt_string: str | None) -> str:
    """Format an ISO datetime string to a readable short form."""
    if not dt_string:
        return "-"
    # Handle ISO format like "2026-01-22T08:00:00-07:00"
    if "T" in dt_string:
        date_part, time_part = dt_string.split("T", 1)
        # Strip timezone offset for display
        time_clean = time_part.split("-")[0].split("+")[0]
        # Remove seconds if present
        if time_clean.count(":") >= 2:
            time_clean = ":".join(time_clean.split(":")[:2])
        return f"{date_part} {time_clean}"
    return dt_string
