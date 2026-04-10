"""Shared input validation and security utilities for all SAGE tools.

Eliminates duplicate validation logic (DRY) and enforces consistent
input sanitization, bounds checking, and error formatting.
"""

from __future__ import annotations

import json
import logging
import re
import sys

# ── Constraints ──────────────────────────────────────────────────────────
MAX_RESULTS_UPPER_BOUND: int = 50
MAX_QUERY_LENGTH: int = 500
MAX_ARXIV_IDS: int = 20
ARXIV_ID_PATTERN: re.Pattern[str] = re.compile(r"^[0-9]{4}\.[0-9]{4,5}(v[0-9]+)?$")

logger = logging.getLogger("sage")


def read_stdin() -> str:
    """Read and strip stdin, returning raw text."""
    return sys.stdin.read().strip()


def parse_json_input(raw: str) -> dict[str, object] | None:
    """Parse JSON from raw string. Returns None and prints error on failure."""
    if not raw:
        emit_error("No input provided. Expected JSON on stdin.")
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            emit_error("Input must be a JSON object.")
            return None
        return data
    except json.JSONDecodeError as exc:
        emit_error(f"Invalid JSON: {exc.msg} at position {exc.pos}")
        return None


def validate_query(query: str, field_name: str = "query") -> str | None:
    """Validate a freeform text query. Returns sanitised string or None."""
    if not query or not query.strip():
        emit_error(f"{field_name} is required")
        return None
    query = query.strip()
    if len(query) > MAX_QUERY_LENGTH:
        emit_error(
            f"{field_name} exceeds maximum length of {MAX_QUERY_LENGTH} characters"
        )
        return None
    return query


def validate_max_results(value: object) -> int:
    """Clamp max_results to safe bounds. Always returns a valid int."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 5
    return max(1, min(n, MAX_RESULTS_UPPER_BOUND))


def validate_arxiv_ids(raw_ids: str) -> list[str] | None:
    """Parse and validate comma-separated arxiv IDs. Returns list or None."""
    if not raw_ids or not raw_ids.strip():
        emit_error("arxiv_id is required")
        return None

    ids = [i.strip() for i in str(raw_ids).split(",") if i.strip()]

    if len(ids) > MAX_ARXIV_IDS:
        emit_error(f"Too many IDs. Maximum is {MAX_ARXIV_IDS}, got {len(ids)}.")
        return None

    validated: list[str] = []
    for aid in ids:
        if not ARXIV_ID_PATTERN.match(aid):
            emit_error(f"Invalid arxiv ID format: '{aid}'. Expected pattern YYMM.NNNNN")
            return None
        validated.append(aid)

    return validated


def emit_error(message: str) -> None:
    """Print a JSON error to stdout (agent-consumable) and log it."""
    # Redact implementation details from error messages
    safe_message = message.replace(str(sys.executable), "<python>")
    print(json.dumps({"error": safe_message}))
    logger.warning("Tool error: %s", message)


def emit_json(data: object) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, indent=2))
