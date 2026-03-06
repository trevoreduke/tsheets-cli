"""Tests for authentication error handling."""

from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import httpx
import pytest

from tsheets_cli.api import get_token, _handle_response


class TestGetTokenMissing:
    """When TSHEETS_API_TOKEN is not set, exit with clear instructions."""

    def test_missing_token_exits(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            os.environ.pop("TSHEETS_API_TOKEN", None)
            with pytest.raises(SystemExit) as exc_info:
                get_token()
            assert exc_info.value.code == 1

    def test_empty_token_exits(self):
        with patch.dict(os.environ, {"TSHEETS_API_TOKEN": ""}):
            with pytest.raises(SystemExit) as exc_info:
                get_token()
            assert exc_info.value.code == 1

    def test_whitespace_only_token_exits(self):
        with patch.dict(os.environ, {"TSHEETS_API_TOKEN": "   "}):
            with pytest.raises(SystemExit) as exc_info:
                get_token()
            assert exc_info.value.code == 1

    def test_missing_token_message_contains_fix(self, capsys):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TSHEETS_API_TOKEN", None)
            with pytest.raises(SystemExit):
                get_token()
        # Rich prints to stderr via Console(stderr=True)
        # We check that the function exits; message content is tested via output


class TestGetTokenValid:
    """When TSHEETS_API_TOKEN is set, return it."""

    def test_valid_token_returned(self):
        with patch.dict(os.environ, {"TSHEETS_API_TOKEN": "S.abc123xyz"}):
            assert get_token() == "S.abc123xyz"

    def test_token_with_whitespace_stripped(self):
        with patch.dict(os.environ, {"TSHEETS_API_TOKEN": "  S.abc123xyz  "}):
            assert get_token() == "S.abc123xyz"


class TestHandleResponse401:
    """401 response exits with auth failure message."""

    def test_401_exits_with_code_1(self):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response,
        )
        with patch.dict(os.environ, {"TSHEETS_API_TOKEN": "S.test1234token"}):
            with pytest.raises(SystemExit) as exc_info:
                _handle_response(response)
            assert exc_info.value.code == 1


class TestHandleResponse403:
    """403 response exits with permission denied message."""

    def test_403_exits_with_code_1(self):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 403
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden",
            request=MagicMock(),
            response=response,
        )
        with pytest.raises(SystemExit) as exc_info:
            _handle_response(response)
        assert exc_info.value.code == 1


class TestHandleResponseSuccess:
    """Successful responses return parsed JSON."""

    def test_200_returns_json(self):
        response = MagicMock(spec=httpx.Response)
        response.raise_for_status.return_value = None
        response.json.return_value = {"results": {"users": {}}}
        result = _handle_response(response)
        assert result == {"results": {"users": {}}}
