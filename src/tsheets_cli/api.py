"""TSheets API client with auth, error handling, and request helpers."""

from __future__ import annotations

import os
import ssl
import sys
from typing import Any, Callable

import httpx
from rich.console import Console

console = Console(stderr=True)

API_BASE_URL = "https://rest.tsheets.com/api/v1"
REQUEST_TIMEOUT = 30.0


def get_token() -> str:
    """Get the API token from the environment, or exit with a helpful message."""
    token = os.environ.get("TSHEETS_API_TOKEN", "").strip()
    if not token:
        console.print(
            "[bold red]Error:[/] TSHEETS_API_TOKEN environment variable is not set.\n"
            "\n"
            "[yellow]To fix, set your TSheets/QuickBooks Time API token:[/]\n"
            "\n"
            "  [green]export TSHEETS_API_TOKEN='S.xxxxxxxxxxxxxxxxxxxx'[/]\n"
            "\n"
            "For persistence, add it to your shell profile:\n"
            "\n"
            "  [dim]echo 'export TSHEETS_API_TOKEN=\"your-token\"' >> ~/.zshrc[/]\n"
            "\n"
            "Get your token from: [link]https://tsheetsteam.tsheets.com/api-addons[/]\n"
            "Or ask your TSheets admin for the shared company API token."
        )
        sys.exit(1)
    return token


def _client() -> httpx.Client:
    """Create a configured httpx client."""
    token = get_token()
    return httpx.Client(
        base_url=API_BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=REQUEST_TIMEOUT,
    )


def _handle_response(response: httpx.Response) -> dict[str, Any]:
    """Handle API response, raising clear errors for failures."""
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 401:
            token = os.environ.get("TSHEETS_API_TOKEN", "")
            masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
            console.print(
                "[bold red]Authentication failed (401 Unauthorized).[/]\n"
                "\n"
                f"  Token in use: [dim]{masked}[/]\n"
                "\n"
                "[yellow]Possible causes:[/]\n"
                "  1. Token is invalid or was revoked\n"
                "  2. Token has expired\n"
                "  3. Token was copy-pasted with extra whitespace or quotes\n"
                "\n"
                "[yellow]To fix:[/]\n"
                "  • Verify your token at [link]https://tsheetsteam.tsheets.com/api-addons[/]\n"
                "  • Re-export it: [green]export TSHEETS_API_TOKEN='S.xxxx...'[/]\n"
                "  • Or ask your TSheets admin for a fresh token."
            )
            sys.exit(1)
        elif status == 403:
            console.print(
                "[bold red]Access denied (403 Forbidden).[/]\n"
                "\n"
                "Your API token is valid but lacks permission for this operation.\n"
                "\n"
                "[yellow]To fix:[/]\n"
                "  • Ask your TSheets admin to grant the required permissions.\n"
                "  • Some endpoints require admin-level tokens."
            )
            sys.exit(1)
        elif status == 417:
            # TSheets uses 417 for validation errors
            body = exc.response.json() if exc.response.content else {}
            console.print(f"[bold red]Validation error (417):[/] {body}")
            sys.exit(1)
        elif status == 429:
            retry_after = exc.response.headers.get("Retry-After", "60")
            console.print(
                f"[bold red]Rate limited (429 Too Many Requests).[/]\n"
                "\n"
                f"The TSheets API rate limit has been exceeded.\n"
                f"[yellow]Wait {retry_after} seconds and try again.[/]"
            )
            sys.exit(1)
        elif status >= 500:
            console.print(
                f"[bold red]TSheets server error ({status}).[/] Try again in a few minutes.\n"
                "[yellow]Check service status: https://status.quickbooks.intuit.com[/]"
            )
            sys.exit(1)
        else:
            body = exc.response.text
            console.print(f"[bold red]API error ({status}):[/] {body}")
            sys.exit(1)

    # Parse JSON safely — the API should always return JSON, but guard against edge cases
    try:
        return response.json()
    except (ValueError, TypeError):
        console.print(
            "[bold red]Unexpected response.[/] The API returned non-JSON data.\n"
            f"[dim]Status: {response.status_code} | Content-Type: "
            f"{response.headers.get('content-type', 'unknown')}[/]\n"
            "[yellow]This may indicate a temporary API issue. Try again shortly.[/]"
        )
        sys.exit(1)


def _handle_network_errors(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Execute an API call function with comprehensive network error handling.

    Wraps the provided callable and catches all transport-level errors from httpx,
    printing actionable error messages before exiting.

    Args:
        fn: A zero-argument callable that performs the HTTP request and returns
            the parsed response dict.

    Returns:
        The parsed JSON response dict on success.

    Raises:
        SystemExit: On any network or transport error, after printing a
            user-friendly message to stderr.
    """
    try:
        return fn()
    except httpx.ConnectError as exc:
        # DNS resolution failures, connection refused, etc.
        detail = str(exc)
        if "Name or service not known" in detail or "getaddrinfo" in detail or "nodename nor servname" in detail:
            console.print(
                "[bold red]DNS resolution failed.[/] Could not resolve rest.tsheets.com.\n"
                "\n"
                "[yellow]Possible causes:[/]\n"
                "  1. No internet connection\n"
                "  2. DNS server is unreachable\n"
                "  3. VPN or firewall blocking DNS\n"
                "\n"
                "[yellow]Try:[/]\n"
                "  • Check your internet connection\n"
                "  • Try: [dim]nslookup rest.tsheets.com[/]\n"
                "  • Switch DNS to 8.8.8.8 or 1.1.1.1 if needed"
            )
        elif "Connection refused" in detail:
            console.print(
                "[bold red]Connection refused.[/] rest.tsheets.com is not accepting connections.\n"
                "\n"
                "[yellow]This is likely a temporary issue or a proxy/firewall problem.[/]\n"
                "Check service status: https://status.quickbooks.intuit.com"
            )
        else:
            console.print(
                "[bold red]Connection error.[/] Could not reach rest.tsheets.com.\n"
                "\n"
                "[yellow]Check your internet connection and try again.[/]\n"
                f"[dim]Detail: {detail}[/]"
            )
        sys.exit(1)
    except httpx.TimeoutException:
        console.print(
            f"[bold red]Request timed out[/] after {REQUEST_TIMEOUT:.0f}s.\n"
            "The TSheets API did not respond in time.\n"
            "\n"
            "[yellow]Possible causes:[/]\n"
            "  1. Slow or unstable internet connection\n"
            "  2. TSheets API is experiencing high load\n"
            "\n"
            "[yellow]Try again or check: https://status.quickbooks.intuit.com[/]"
        )
        sys.exit(1)
    except ssl.SSLError as exc:
        console.print(
            "[bold red]SSL/TLS error.[/] Secure connection to rest.tsheets.com failed.\n"
            "\n"
            "[yellow]Possible causes:[/]\n"
            "  1. Corporate proxy intercepting HTTPS traffic\n"
            "  2. System clock is wrong (certificates are time-sensitive)\n"
            "  3. Outdated SSL certificates on this machine\n"
            "\n"
            f"[dim]Detail: {exc}[/]"
        )
        sys.exit(1)
    except httpx.RequestError as exc:
        # Catch-all for any other transport-level httpx errors
        # (e.g., ReadError, WriteError, PoolTimeout, NetworkError subtypes)
        console.print(
            f"[bold red]Network error.[/] Request to TSheets API failed.\n"
            "\n"
            f"[dim]Error type: {type(exc).__name__}[/]\n"
            f"[dim]Detail: {exc}[/]\n"
            "\n"
            "[yellow]Check your internet connection and try again.[/]"
        )
        sys.exit(1)


def api_get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make a GET request to the TSheets API."""
    def _do_request() -> dict[str, Any]:
        with _client() as client:
            resp = client.get(endpoint, params=params)
            return _handle_response(resp)
    return _handle_network_errors(_do_request)


def api_post(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make a POST request to the TSheets API."""
    def _do_request() -> dict[str, Any]:
        with _client() as client:
            resp = client.post(endpoint, json=data)
            return _handle_response(resp)
    return _handle_network_errors(_do_request)


def api_put(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make a PUT request to the TSheets API."""
    def _do_request() -> dict[str, Any]:
        with _client() as client:
            resp = client.put(endpoint, json=data)
            return _handle_response(resp)
    return _handle_network_errors(_do_request)


def api_delete(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make a DELETE request to the TSheets API."""
    def _do_request() -> dict[str, Any]:
        with _client() as client:
            resp = client.delete(endpoint, params=params)
            return _handle_response(resp)
    return _handle_network_errors(_do_request)
