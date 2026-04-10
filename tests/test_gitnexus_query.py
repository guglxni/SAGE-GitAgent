"""Unit tests for sage.gitnexus_query — mocked subprocess, no npx calls."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from sage.gitnexus_query import main, run_gitnexus_query


class TestRunGitnexusQuery:
    """Unit tests for run_gitnexus_query()."""

    def test_successful_query(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"symbols": [{"name": "Model"}]}'

        with patch("sage.gitnexus_query.subprocess.run", return_value=mock_result) as mock_run:
            output = run_gitnexus_query("PyTorch model classes")

        assert "Model" in output
        # Verify the version is pinned
        call_args = mock_run.call_args[0][0]
        assert "gitnexus@0.22.2" in call_args

    def test_non_zero_exit(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "index not found"

        with (
            patch("sage.gitnexus_query.subprocess.run", return_value=mock_result),
            pytest.raises(subprocess.CalledProcessError),
        ):
            run_gitnexus_query("anything")

    def test_timeout(self) -> None:
        with patch(
            "sage.gitnexus_query.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="gitnexus", timeout=120),
        ), pytest.raises(subprocess.TimeoutExpired):
            run_gitnexus_query("slow query")


class TestMainEntryPoint:
    """Unit tests for the main() stdin→stdout flow."""

    def test_main_missing_query(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sage.gitnexus_query.read_stdin", return_value='{}'):
            main()
        captured = json.loads(capsys.readouterr().out)
        assert "query is required" in captured["error"]

    def test_main_query_too_long(self, capsys: pytest.CaptureFixture[str]) -> None:
        long_q = "a" * 501
        with patch("sage.gitnexus_query.read_stdin", return_value=json.dumps({"query": long_q})):
            main()
        captured = json.loads(capsys.readouterr().out)
        assert "exceeds maximum length" in captured["error"]

    def test_main_npx_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("sage.gitnexus_query.read_stdin", return_value='{"query": "test"}'),
            patch("sage.gitnexus_query.run_gitnexus_query", side_effect=FileNotFoundError),
        ):
            main()
        captured = json.loads(capsys.readouterr().out)
        assert "npx not found" in captured["error"]

    def test_main_timeout(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("sage.gitnexus_query.read_stdin", return_value='{"query": "test"}'),
            patch(
                "sage.gitnexus_query.run_gitnexus_query",
                side_effect=subprocess.TimeoutExpired(cmd="g", timeout=120),
            ),
        ):
            main()
        captured = json.loads(capsys.readouterr().out)
        assert "timed out" in captured["error"]
