"""Integration tests — hit real external APIs.

Run with: uv run pytest -m integration
Skip with: uv run pytest -m "not integration"
"""

import pytest

from sage.arxiv_search import search_arxiv
from sage.fetch_abstract import fetch_papers


@pytest.mark.integration
class TestArxivSearchIntegration:
    """Live API tests for arxiv_search."""

    @pytest.mark.asyncio
    async def test_real_search(self) -> None:
        result = await search_arxiv("transformer attention", max_results=2)
        assert "<?xml" in result
        assert "entry" in result.lower()

    @pytest.mark.asyncio
    async def test_search_returns_relevant_content(self) -> None:
        result = await search_arxiv("gradient clipping deep learning", max_results=1)
        assert "<?xml" in result


@pytest.mark.integration
class TestFetchAbstractIntegration:
    """Live API tests for fetch_abstract."""

    @pytest.mark.asyncio
    async def test_fetch_single_paper(self) -> None:
        results = await fetch_papers(["1706.03762"])
        assert len(results) == 1
        assert "Attention Is All You Need" in results[0]

    @pytest.mark.asyncio
    async def test_fetch_multiple_concurrent(self) -> None:
        results = await fetch_papers(["1706.03762", "2310.01848"])
        assert len(results) == 2
        # Both should be valid XML
        assert all("<?xml" in r for r in results)
