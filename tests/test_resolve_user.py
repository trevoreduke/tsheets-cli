"""Tests for user name resolution."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tsheets_cli.resolve import resolve_user


MOCK_USERS_RESPONSE = {
    "results": {
        "users": {
            "101": {
                "id": 101,
                "first_name": "Trevor",
                "last_name": "Duke",
                "active": True,
            },
            "102": {
                "id": 102,
                "first_name": "Jane",
                "last_name": "Smith",
                "active": True,
            },
            "103": {
                "id": 103,
                "first_name": "John",
                "last_name": "Smith",
                "active": False,
            },
            "104": {
                "id": 104,
                "first_name": "Trevor",
                "last_name": "Anderson",
                "active": True,
            },
        }
    }
}


class TestResolveUserNumericID:
    """When a numeric ID is passed, return it directly without API call."""

    def test_numeric_id_returned_directly(self):
        # No API call should be made
        result = resolve_user("12345")
        assert result == 12345

    def test_numeric_id_zero(self):
        result = resolve_user("0")
        assert result == 0


class TestResolveUserExactMatch:
    """Exact full name match returns the user ID."""

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_exact_match_case_insensitive(self, mock_get):
        result = resolve_user("trevor duke")
        assert result == 101
        # resolve_user paginates, so the first (and here only) page is requested
        # with page=1 alongside the active filter.
        mock_get.assert_called_once_with(
            "/users", params={"active": "both", "page": 1}
        )

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_exact_match_preserves_case(self, mock_get):
        result = resolve_user("Trevor Duke")
        assert result == 101

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_exact_match_uppercase(self, mock_get):
        result = resolve_user("JANE SMITH")
        assert result == 102


class TestResolveUserPartialMatch:
    """Single partial match returns that user's ID."""

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_partial_match_last_name_unique(self, mock_get):
        # "Duke" only matches Trevor Duke
        result = resolve_user("Duke")
        assert result == 101

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_partial_match_first_name_unique(self, mock_get):
        # "Jane" only matches Jane Smith
        result = resolve_user("Jane")
        assert result == 102


class TestResolveUserAmbiguous:
    """Multiple partial matches cause exit with helpful message."""

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_ambiguous_name_exits(self, mock_get):
        # "Smith" matches both Jane Smith and John Smith
        with pytest.raises(SystemExit) as exc_info:
            resolve_user("Smith")
        assert exc_info.value.code == 1

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_ambiguous_first_name_exits(self, mock_get):
        # "Trevor" matches Trevor Duke and Trevor Anderson
        with pytest.raises(SystemExit) as exc_info:
            resolve_user("Trevor")
        assert exc_info.value.code == 1


class TestResolveUserNotFound:
    """No match causes exit with helpful message."""

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_not_found_exits(self, mock_get):
        with pytest.raises(SystemExit) as exc_info:
            resolve_user("Nobody Here")
        assert exc_info.value.code == 1

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_empty_results(self, mock_get):
        mock_get.return_value = {"results": {"users": {}}}
        with pytest.raises(SystemExit) as exc_info:
            resolve_user("Anyone")
        assert exc_info.value.code == 1


class TestResolveUserWhitespace:
    """Whitespace handling."""

    @patch("tsheets_cli.resolve.api_get", return_value=MOCK_USERS_RESPONSE)
    def test_leading_trailing_whitespace_stripped(self, mock_get):
        result = resolve_user("  Trevor Duke  ")
        assert result == 101


class TestResolveUserPagination:
    """Users beyond the first page are still resolvable."""

    # Page 1: 50-user limit reached, "more" is True. The target user lives on
    # page 2, so a single un-paginated request would silently fail to find them.
    PAGE_ONE = {
        "results": {
            "users": {
                "201": {
                    "id": 201,
                    "first_name": "Alice",
                    "last_name": "Anderson",
                    "active": True,
                }
            }
        },
        "more": True,
    }
    PAGE_TWO = {
        "results": {
            "users": {
                "202": {
                    "id": 202,
                    "first_name": "Bob",
                    "last_name": "Builder",
                    "active": True,
                }
            }
        },
        "more": False,
    }

    @patch("tsheets_cli.resolve.api_get")
    def test_resolves_user_on_second_page(self, mock_get):
        mock_get.side_effect = [self.PAGE_ONE, self.PAGE_TWO]
        result = resolve_user("Bob Builder")
        assert result == 202
        # Both pages must have been fetched.
        assert mock_get.call_count == 2
        mock_get.assert_any_call("/users", params={"active": "both", "page": 1})
        mock_get.assert_any_call("/users", params={"active": "both", "page": 2})

    @patch("tsheets_cli.resolve.api_get")
    def test_stops_paginating_when_more_false(self, mock_get):
        # When the first page already reports more=False, no second request.
        single_page = {
            "results": {
                "users": {
                    "203": {
                        "id": 203,
                        "first_name": "Carol",
                        "last_name": "Carter",
                        "active": True,
                    }
                }
            },
            "more": False,
        }
        mock_get.return_value = single_page
        result = resolve_user("Carol Carter")
        assert result == 203
        assert mock_get.call_count == 1
