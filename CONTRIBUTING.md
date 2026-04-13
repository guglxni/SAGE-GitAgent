# Contributing to SAGE

Thank you for your interest in contributing to SAGE. This document covers how to get started, what to work on, and what to expect from the process.

## What SAGE Is

SAGE is a GitAgent — an AI agent that lives inside a repository and operates on it. Its architecture is defined by the [open GitAgent standard](https://github.com/open-gitagent/gitagent): `agent.yaml` for the manifest, `SOUL.md` for identity, `RULES.md` for constraints, and `SKILL.md` files for capabilities.

Before contributing, spend a few minutes reading `SOUL.md` and `RULES.md`. They define what SAGE is and isn't allowed to do. Any contribution that violates those boundaries won't be merged.

---

## Ways to Contribute

### Bug Reports
Open an issue with:
- What you ran (exact command or prompt)
- What you expected
- What actually happened (including any output files that were produced)
- The target repo you ran SAGE against (or a minimal reproduction)

### Improving Skills
Skills live in `skills/<skill-name>/SKILL.md`. They're YAML-frontmatter markdown files describing what the skill does, how it runs, and what it outputs.

Good skill improvements:
- Sharpen the output format (make TECHNIQUES.md entries more consistent)
- Add edge-case handling (empty repos, non-ML repos, very large repos)
- Improve the arXiv query construction logic in `hunt-papers`
- Better severity classification logic in `identify-gaps`

### Improving Tools
Tools live in `tools/<tool-name>/`. Each tool has a YAML schema (`*.yaml`) and a Python implementation (`*.py`).

Good tool improvements:
- Better error handling for arXiv API timeouts
- More robust XML parsing for edge-case arXiv responses
- Performance improvements for `gitnexus-query` on large repos
- Better batch handling in `fetch-abstract`

### Knowledge Base
The knowledge base lives in `knowledge/`. These files are loaded by the agent at runtime.

Good knowledge base improvements:
- Add new ML techniques to `ml-techniques-taxonomy.md`
- Add new arXiv categories to `arxiv-categories.md`
- Refine the severity decision tree in `severity-classification-guide.md`

### HuggingFace Space (`hf-space-demo/`)
The Space is a Streamlit frontend that wraps the SAGE pipeline. Improvements welcome:
- Better progress indicators during the 3-step pipeline
- Download buttons for output files
- Better error messages when the LLM key is wrong or rate-limited

---

## Development Setup

```bash
# Clone the repo
git clone https://github.com/guglxni/SAGE-GitAgent.git
cd SAGE-GitAgent

# Install Python dependencies
uv sync --all-groups
uv pip install -e .

# Run the tests
uv run pytest tests/ -v

# Test tools individually
echo '{"search_query": "attention is all you need", "max_results": 3}' | uv run python tools/arxiv-search.py
echo '{"arxiv_id": "1706.03762"}' | uv run python tools/fetch-abstract.py
```

To run the full pipeline against a real repo:
```bash
git clone https://github.com/karpathy/minGPT.git /tmp/test-repo
npx gitclaw --dir /tmp/test-repo --prompt "Run the full SAGE pipeline on this codebase."
```

---

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes, keeping them scoped to one concern
3. Run `uv run pytest tests/ -v` — all tests must pass
4. Run `uv run ruff check .` — no lint errors
5. Open a PR with a clear description of what changed and why

PRs that modify `agent.yaml`, `SOUL.md`, or `RULES.md` require extra justification — these files define the agent's identity and boundaries.

---

## Code Style

- Python 3.12+ with type hints where it helps clarity
- `ruff` for linting (config in `pyproject.toml`, 100-char line limit)
- No external dependencies beyond what's in `pyproject.toml`
- Tools must be executable as standalone scripts via stdin/stdout JSON

---

## Questions

Open a GitHub Discussion or file an issue with the `question` label.
