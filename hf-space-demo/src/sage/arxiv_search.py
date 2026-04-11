"""arxiv-search tool — queries the arXiv API for papers matching a search query.

Reads JSON from stdin, writes arXiv Atom XML to stdout.
"""

from __future__ import annotations

import asyncio
from urllib.parse import quote_plus

import httpx

from sage.validation import (
    parse_json_input,
    read_stdin,
    validate_max_results,
    validate_query,
)

# ── Constants ────────────────────────────────────────────────────────────
ARXIV_API_BASE: str = "https://export.arxiv.org/api/query"
DEFAULT_TIMEOUT: float = 30.0


async def search_arxiv(query: str, max_results: int = 5) -> str:
    """Execute an arXiv API search and return raw XML response.

    Args:
        query: The search term (will be URL-encoded).
        max_results: Number of results to return (clamped 1-50).

    Returns:
        Raw XML string from the arXiv API.

    Raises:
        httpx.HTTPError: If the API request fails.
    """
    encoded_query = quote_plus(query)
    url = (
        f"{ARXIV_API_BASE}?search_query=all:{encoded_query}"
        f"&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.text


async def main() -> None:
    """Entry point: read stdin JSON, validate, query arXiv, print result."""
    raw = read_stdin()
    params = parse_json_input(raw)
    if params is None:
        return

    query = validate_query(params.get("search_query", ""), field_name="search_query")
    if query is None:
        return

    max_results = validate_max_results(params.get("max_results", 5))

    try:
        result = await search_arxiv(query, max_results)
        print(result)
    except httpx.HTTPError as exc:
        from sage.validation import emit_error
        emit_error(f"arXiv API request failed: {type(exc).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
