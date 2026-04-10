"""gitnexus-query tool — queries the GitNexus AST knowledge graph.

Reads JSON from stdin, executes gitnexus CLI, writes results to stdout.
Pins gitnexus version and sanitises user input against command injection.
"""

from __future__ import annotations

import subprocess

from sage.validation import (
    emit_error,
    parse_json_input,
    read_stdin,
    validate_query,
)

# ── Constants ────────────────────────────────────────────────────────────
GITNEXUS_PACKAGE: str = "gitnexus@0.22.2"  # pinned version — no @latest
GITNEXUS_TIMEOUT: int = 120


def run_gitnexus_query(query: str) -> str:
    """Execute a GitNexus CLI query in a subprocess.

    Args:
        query: Sanitised search query string.

    Returns:
        Stdout from the gitnexus process.

    Raises:
        subprocess.TimeoutExpired: If the query takes too long.
        subprocess.CalledProcessError: If gitnexus exits non-zero.
    """
    # shlex.quote prevents shell injection — query is never interpolated
    # into a shell string; it's passed as a direct argv element
    result = subprocess.run(
        ["npx", "-y", GITNEXUS_PACKAGE, "query", query],
        capture_output=True,
        text=True,
        timeout=GITNEXUS_TIMEOUT,
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, "gitnexus", result.stderr
        )

    return result.stdout


def main() -> None:
    """Entry point: read stdin JSON, validate, query GitNexus, print result."""
    raw = read_stdin()
    params = parse_json_input(raw)
    if params is None:
        return

    query = validate_query(params.get("query", ""))
    if query is None:
        return

    try:
        output = run_gitnexus_query(query)
        print(output)
    except subprocess.TimeoutExpired:
        emit_error("GitNexus query timed out.")
    except subprocess.CalledProcessError:
        emit_error("GitNexus query failed.")
    except FileNotFoundError:
        emit_error("npx not found. Ensure Node.js is installed.")


if __name__ == "__main__":
    main()
