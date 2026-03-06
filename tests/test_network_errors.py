"""Tests for network error handling in the API client.

Validates that all transport-level errors (DNS, timeout, SSL, connection refused,
rate limiting, non-JSON responses, etc.) produce clear, actionable error messages
and exit with code 1.
"""

from __future__ import annotations

import os
import ssl
from unittest.mock import MagicMock, patch

import httpx
import pytest

from tsheets_cli.api import (
    _handle_network_errors,
    _handle_response,
    api_get,
    api_post,
    api_put,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_env():
    """Patch env so get_token() succeeds."""
    return patch.dict(os.environ, {"TSHEETS_API_TOKEN": "S.test1234token"})


def _mock_response(status_code: int = 200, json_data=None, text="", headers=None, content=b"{}"):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    resp.content = content
    resp.headers = headers or {}
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.return_value = {}
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# Connection errors
# ---------------------------------------------------------------------------

class TestConnectionError:
    """httpx.ConnectError produces a clear message and exits."""

    def test_generic_connect_error_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(httpx.ConnectError("Connection failed"))
                )
            assert exc_info.value.code == 1

    def test_dns_resolution_failure_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(
                        httpx.ConnectError("Name or service not known")
                    )
                )
            assert exc_info.value.code == 1

    def test_dns_nodename_failure_exits(self):
        """macOS-style DNS error message."""
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(
                        httpx.ConnectError("nodename nor servname provided")
                    )
                )
            assert exc_info.value.code == 1

    def test_connection_refused_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(
                        httpx.ConnectError("Connection refused")
                    )
                )
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Timeout errors
# ---------------------------------------------------------------------------

class TestTimeoutError:
    """httpx.TimeoutException produces a clear message and exits."""

    def test_timeout_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(httpx.TimeoutException("timed out"))
                )
            assert exc_info.value.code == 1

    def test_connect_timeout_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(httpx.ConnectTimeout("connect timed out"))
                )
            assert exc_info.value.code == 1

    def test_read_timeout_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(httpx.ReadTimeout("read timed out"))
                )
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# SSL errors
# ---------------------------------------------------------------------------

class TestSSLError:
    """SSL/TLS errors produce a clear message and exit."""

    def test_ssl_error_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(
                        ssl.SSLError("certificate verify failed")
                    )
                )
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Generic request errors (catch-all)
# ---------------------------------------------------------------------------

class TestGenericRequestError:
    """Other httpx.RequestError subtypes are caught gracefully."""

    def test_read_error_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(
                        httpx.ReadError("connection reset by peer")
                    )
                )
            assert exc_info.value.code == 1

    def test_pool_timeout_exits(self):
        with _mock_env():
            with pytest.raises(SystemExit) as exc_info:
                _handle_network_errors(
                    lambda: (_ for _ in ()).throw(
                        httpx.PoolTimeout("pool timeout")
                    )
                )
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Rate limiting (429)
# ---------------------------------------------------------------------------

class TestRateLimiting:
    """429 responses show retry guidance and exit."""

    def test_429_exits_with_retry_after(self):
        response = _mock_response(status_code=429, headers={"Retry-After": "30"})
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=response,
        )
        with pytest.raises(SystemExit) as exc_info:
            _handle_response(response)
        assert exc_info.value.code == 1

    def test_429_without_retry_header(self):
        response = _mock_response(status_code=429, headers={})
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=response,
        )
        with pytest.raises(SystemExit) as exc_info:
            _handle_response(response)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Non-JSON responses
# ---------------------------------------------------------------------------

class TestNonJSONResponse:
    """When the API returns non-JSON, we exit gracefully."""

    def test_non_json_response_exits(self):
        response = _mock_response(status_code=200)
        response.json.side_effect = ValueError("No JSON object could be decoded")
        response.headers = {"content-type": "text/html"}
        with pytest.raises(SystemExit) as exc_info:
            _handle_response(response)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Server errors (5xx)
# ---------------------------------------------------------------------------

class TestServerErrors:
    """5xx errors show service status link and exit."""

    @pytest.mark.parametrize("status", [500, 502, 503, 504])
    def test_5xx_exits(self, status):
        response = _mock_response(status_code=status)
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"{status} Server Error",
            request=MagicMock(),
            response=response,
        )
        with pytest.raises(SystemExit) as exc_info:
            _handle_response(response)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Integration: api_get / api_post / api_put with network errors
# ---------------------------------------------------------------------------

class TestApiMethodsNetworkErrors:
    """Verify api_get, api_post, api_put all route through _handle_network_errors."""

    @patch("tsheets_cli.api._client")
    def test_api_get_connect_error(self, mock_client_fn):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(side_effect=httpx.ConnectError("fail"))
        ctx.__exit__ = MagicMock(return_value=False)
        mock_client_fn.return_value = ctx
        with _mock_env(), pytest.raises(SystemExit) as exc_info:
            api_get("/users")
        assert exc_info.value.code == 1

    @patch("tsheets_cli.api._client")
    def test_api_post_timeout(self, mock_client_fn):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(side_effect=httpx.TimeoutException("timeout"))
        ctx.__exit__ = MagicMock(return_value=False)
        mock_client_fn.return_value = ctx
        with _mock_env(), pytest.raises(SystemExit) as exc_info:
            api_post("/timesheets", {"data": []})
        assert exc_info.value.code == 1

    @patch("tsheets_cli.api._client")
    def test_api_put_ssl_error(self, mock_client_fn):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(side_effect=ssl.SSLError("cert failed"))
        ctx.__exit__ = MagicMock(return_value=False)
        mock_client_fn.return_value = ctx
        with _mock_env(), pytest.raises(SystemExit) as exc_info:
            api_put("/timesheets", {"data": []})
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Success path still works
# ---------------------------------------------------------------------------

class TestSuccessPath:
    """Happy path: _handle_network_errors returns the result on success."""

    def test_successful_call_returns_data(self):
        result = _handle_network_errors(lambda: {"results": {"users": {}}})
        assert result == {"results": {"users": {}}}
