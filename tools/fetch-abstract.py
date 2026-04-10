"""Thin CLI entry point for fetch-abstract tool."""
import sys
import os

# Allow running from any directory -- add src/ to path if sage not installed
_here = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(os.path.dirname(_here), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

import asyncio
from sage.fetch_abstract import main

if __name__ == "__main__":
    asyncio.run(main())
