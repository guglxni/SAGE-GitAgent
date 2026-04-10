"""Unit tests for sage.arxiv_search — mocked, no network calls."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from sage.arxiv_search import main, search_arxiv


class TestSearchArxiv:
    """Unit tests for the search_arxiv() function."""

    @pytest.mark.asyncio
    async def test_successful_search(self) -> None:
        mock_response = MagicMock()
        mock_response.text = "<feed><entry><title>Test Paper</title></entry></feed>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sage.arxiv_search.httpx.AsyncClient", return_value=mock_client):
            result = await search_arxiv("attention mechanism", max_results=2)

        assert "<feed>" in result
        assert "Test Paper" in result
        mock_client.get.assert_called_once()
        call_url = mock_client.get.call_args[0][0]
        assert "attention+mechanism" in call_url
        assert "max_results=2" in call_url

    @pytest.mark.asyncio
    async def test_http_error_propagates(self) -> None:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        ))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("sage.arxiv_search.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await search_arxiv("nonexistent")


class TestMainEntryPoint:
    """Unit tests for the main() stdin→stdout flow."""

    @pytest.mark.asyncio
    async def test_main_missing_query(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sage.arxiv_search.read_stdin", return_value='{"max_results": 2}'):
            await main()
        captured = json.loads(capsys.readouterr().out)
        assert "search_query is required" in captured["error"]

    @pytest.mark.asyncio
    async def test_main_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sage.arxiv_search.read_stdin", return_value="{broken"):
            await main()
        captured = json.loads(capsys.readouterr().out)
        assert "Invalid JSON" in captured["error"]

    @pytest.mark.asyncio
    async def test_main_query_too_long(self, capsys: pytest.CaptureFixture[str]) -> None:
        long_q = "a" * 501
        payload = json.dumps({"search_query": long_q})
        with patch("sage.arxiv_search.read_stdin", return_value=payload):
            await main()
        captured = json.loads(capsys.readouterr().out)
        assert "exceeds maximum length" in captured["error"]
