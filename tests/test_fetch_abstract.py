"""Unit tests for sage.fetch_abstract — mocked, no network calls."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from sage.fetch_abstract import fetch_papers, fetch_single_paper, main


class TestFetchSinglePaper:
    """Unit tests for fetch_single_paper()."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        mock_response = MagicMock()
        mock_response.text = "<feed><entry><title>Attention</title></entry></feed>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        semaphore = asyncio.Semaphore(5)
        result = await fetch_single_paper(mock_client, "1706.03762", semaphore)

        assert "<feed>" in result
        assert "Attention" in result

    @pytest.mark.asyncio
    async def test_http_error_returns_comment(self) -> None:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("fail"))

        semaphore = asyncio.Semaphore(5)
        result = await fetch_single_paper(mock_client, "0000.00000", semaphore)

        assert "<!-- Failed to fetch" in result
        assert "HTTP error" in result


class TestFetchPapers:
    """Unit tests for fetch_papers() batch processing."""

    @pytest.mark.asyncio
    async def test_concurrent_fetch(self) -> None:
        mock_response = MagicMock()
        mock_response.text = "<feed><entry><title>Paper</title></entry></feed>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sage.fetch_abstract.httpx.AsyncClient", return_value=mock_client):
            results = await fetch_papers(["1706.03762", "2310.01848"])

        assert len(results) == 2
        assert all("<feed>" in r for r in results)

    @pytest.mark.asyncio
    async def test_partial_failure(self) -> None:
        """One paper succeeds, one fails — both should appear in output."""
        call_count = 0

        async def mock_get(url: str, **kwargs) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                resp = MagicMock()
                resp.text = "<feed><entry>OK</entry></feed>"
                resp.raise_for_status = MagicMock()
                return resp
            raise httpx.HTTPError("fail")

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sage.fetch_abstract.httpx.AsyncClient", return_value=mock_client):
            results = await fetch_papers(["1706.03762", "0000.00000"])

        assert len(results) == 2
        assert "<feed>" in results[0]
        assert "Failed to fetch" in results[1]


class TestMainEntryPoint:
    """Unit tests for the main() stdin→stdout flow."""

    @pytest.mark.asyncio
    async def test_main_missing_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sage.fetch_abstract.read_stdin", return_value='{}'):
            await main()
        captured = json.loads(capsys.readouterr().out)
        assert "arxiv_id is required" in captured["error"]

    @pytest.mark.asyncio
    async def test_main_invalid_id_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sage.fetch_abstract.read_stdin", return_value='{"arxiv_id": "not-a-real-id"}'):
            await main()
        captured = json.loads(capsys.readouterr().out)
        assert "Invalid arxiv ID format" in captured["error"]
