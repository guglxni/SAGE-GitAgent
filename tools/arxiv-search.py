"""Thin CLI entry point for arxiv-search tool."""
import asyncio

from sage.arxiv_search import main

if __name__ == "__main__":
    asyncio.run(main())
