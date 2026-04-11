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
GITNEXUS_PACKAGE: str = "gitnexus@1.5.3"  # pinned version — no @latest
GITNEXUS_TIMEOUT: int = 120


def run_gitnexus_query(query: str, repo: str | None = None) -> str:
    """Execute a GitNexus CLI query in a subprocess.

    Args:
        query: Sanitised search query string.
        repo: Optional repo name to target when multiple repos are indexed.

    Returns:
        Stdout from the gitnexus process.

    Raises:
        subprocess.TimeoutExpired: If the query takes too long.
        subprocess.CalledProcessError: If gitnexus exits non-zero.
    """
    cmd = ["npx", "-y", GITNEXUS_PACKAGE, "query", query]
    if repo:
        cmd += ["--repo", repo]
    result = subprocess.run(
        cmd,
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

    repo = params.get("repo") or None

    try:
        output = run_gitnexus_query(query, repo)
        print(output)
    except subprocess.TimeoutExpired:
        emit_error("GitNexus query timed out.")
    except subprocess.CalledProcessError:
        emit_error("GitNexus query failed.")
    except FileNotFoundError:
        emit_error("npx not found. Ensure Node.js is installed.")


if __name__ == "__main__":
    main()
