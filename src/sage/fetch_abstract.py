"""fetch-abstract tool — fetches metadata for one or more arXiv papers.

Reads JSON from stdin, writes arXiv Atom XML to stdout.
Supports concurrent batch fetching with semaphore-based rate limiting.
"""

from __future__ import annotations

import asyncio

import httpx

from sage.validation import (
    emit_error,
    parse_json_input,
    read_stdin,
    validate_arxiv_ids,
)

# ── Constants ────────────────────────────────────────────────────────────
ARXIV_API_BASE: str = "https://export.arxiv.org/api/query"
DEFAULT_TIMEOUT: float = 15.0
MAX_CONCURRENT_REQUESTS: int = 5  # semaphore-based rate limiting


async def fetch_single_paper(
    client: httpx.AsyncClient,
    arxiv_id: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """Fetch metadata for a single arXiv paper with rate limiting.

    Args:
        client: Shared httpx async client.
        arxiv_id: Validated arXiv paper ID.
        semaphore: Concurrency limiter.

    Returns:
        Raw XML string, or an XML comment on failure.
    """
    async with semaphore:
        url = f"{ARXIV_API_BASE}?id_list={arxiv_id}"
        try:
            response = await client.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError:
            return f"<!-- Failed to fetch {arxiv_id}: HTTP error -->"
        except Exception:
            return f"<!-- Failed to fetch {arxiv_id}: unexpected error -->"


async def fetch_papers(arxiv_ids: list[str]) -> list[str]:
    """Fetch metadata for multiple arXiv papers concurrently.

    Args:
        arxiv_ids: List of validated arXiv IDs.

    Returns:
        List of XML response strings (one per ID).
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    async with httpx.AsyncClient() as client:
        tasks = [fetch_single_paper(client, aid, semaphore) for aid in arxiv_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    output: list[str] = []
    for result in results:
        if isinstance(result, Exception):
            output.append(f"<!-- Unhandled exception: {type(result).__name__} -->")
        else:
            output.append(result)
    return output


async def main() -> None:
    """Entry point: read stdin JSON, validate IDs, fetch, print results."""
    raw = read_stdin()
    params = parse_json_input(raw)
    if params is None:
        return

    arxiv_ids = validate_arxiv_ids(params.get("arxiv_id", ""))
    if arxiv_ids is None:
        return

    try:
        results = await fetch_papers(arxiv_ids)
        print("\n".join(results))
    except Exception:
        emit_error("Batch fetch failed unexpectedly.")


if __name__ == "__main__":
    asyncio.run(main())
