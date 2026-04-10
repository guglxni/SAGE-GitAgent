"""Unit tests for sage.validation — the shared validation module.

These are pure unit tests with zero external dependencies.
"""

import json

import pytest

from sage.validation import (
    MAX_ARXIV_IDS,
    MAX_QUERY_LENGTH,
    MAX_RESULTS_UPPER_BOUND,
    parse_json_input,
    validate_arxiv_ids,
    validate_max_results,
    validate_query,
)


class TestParseJsonInput:
    """Tests for parse_json_input()."""

    def test_valid_json(self) -> None:
        result = parse_json_input('{"key": "value"}')
        assert result == {"key": "value"}

    def test_empty_string(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = parse_json_input("")
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "error" in captured

    def test_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = parse_json_input("{broken")
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "Invalid JSON" in captured["error"]

    def test_non_object_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = parse_json_input('[1, 2, 3]')
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "must be a JSON object" in captured["error"]


class TestValidateQuery:
    """Tests for validate_query()."""

    def test_valid_query(self) -> None:
        assert validate_query("transformer attention") == "transformer attention"

    def test_strips_whitespace(self) -> None:
        assert validate_query("  hello  ") == "hello"

    def test_empty_query(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = validate_query("")
        assert result is None

    def test_whitespace_only(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = validate_query("   ")
        assert result is None

    def test_exceeds_max_length(self, capsys: pytest.CaptureFixture[str]) -> None:
        long_query = "a" * (MAX_QUERY_LENGTH + 1)
        result = validate_query(long_query)
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "exceeds maximum length" in captured["error"]

    def test_custom_field_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = validate_query("", field_name="search_query")
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "search_query is required" in captured["error"]


class TestValidateMaxResults:
    """Tests for validate_max_results()."""

    def test_valid_int(self) -> None:
        assert validate_max_results(10) == 10

    def test_string_number(self) -> None:
        assert validate_max_results("7") == 7

    def test_clamp_lower(self) -> None:
        assert validate_max_results(-5) == 1

    def test_clamp_upper(self) -> None:
        assert validate_max_results(9999) == MAX_RESULTS_UPPER_BOUND

    def test_none_returns_default(self) -> None:
        assert validate_max_results(None) == 5

    def test_garbage_returns_default(self) -> None:
        assert validate_max_results("abc") == 5


class TestValidateArxivIds:
    """Tests for validate_arxiv_ids()."""

    def test_single_valid_id(self) -> None:
        result = validate_arxiv_ids("1706.03762")
        assert result == ["1706.03762"]

    def test_multiple_valid_ids(self) -> None:
        result = validate_arxiv_ids("1706.03762, 2310.01848")
        assert result == ["1706.03762", "2310.01848"]

    def test_versioned_id(self) -> None:
        result = validate_arxiv_ids("1706.03762v7")
        assert result == ["1706.03762v7"]

    def test_empty_string(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = validate_arxiv_ids("")
        assert result is None

    def test_invalid_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = validate_arxiv_ids("not-a-real-id")
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "Invalid arxiv ID format" in captured["error"]

    def test_too_many_ids(self, capsys: pytest.CaptureFixture[str]) -> None:
        ids = ", ".join([f"2310.{str(i).zfill(5)}" for i in range(MAX_ARXIV_IDS + 1)])
        result = validate_arxiv_ids(ids)
        assert result is None
        captured = json.loads(capsys.readouterr().out)
        assert "Too many IDs" in captured["error"]
