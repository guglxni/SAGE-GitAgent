"""Thin CLI entry point for fetch-abstract tool."""
import asyncio

from sage.fetch_abstract import main

if __name__ == "__main__":
    asyncio.run(main())
