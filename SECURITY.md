# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | Yes       |
| 1.x     | Critical fixes only |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, send a report to: **security@[your-domain]** (or use GitHub's private vulnerability reporting under the Security tab).

Include:
- A description of the vulnerability
- Steps to reproduce it
- What information or systems it could expose
- Your suggested fix, if you have one

You'll receive an acknowledgment within 48 hours. If the vulnerability is confirmed, a fix will be issued within 14 days for critical issues.

---

## Threat Model

SAGE is a read-only research tool. It is designed with the following security properties:

### What SAGE Does NOT Do
- **Never sends source code to external APIs.** The arXiv API only receives search query strings — never file contents, function bodies, or identifiers from your codebase.
- **Never modifies source code.** SAGE writes only to `TECHNIQUES.md`, `PAPERS.md`, `SUMMARIES.md`, `GAPS.md`, and `RELATED_WORK.md`. This is enforced in `RULES.md`.
- **Never stores credentials.** LLM API keys are passed via environment variables and are never written to disk.
- **Never executes code from the target repo.** Analysis is purely AST-based via GitNexus.

### What SAGE Does
- Queries the public arXiv API (no authentication required) with text search strings derived from detected technique names.
- Runs `npx gitnexus@1.5.3` as a subprocess to build an AST knowledge graph of the local codebase.
- Calls an LLM provider (Groq, OpenAI, Anthropic, or custom) to reason over the analysis results.

### Potential Risk Areas
- **LLM key exposure**: Your API key is passed via environment variable. Do not commit `.env` files. The HuggingFace Space uses Space Secrets — never hard-code keys.
- **Prompt injection via code comments**: A malicious repo could contain comments designed to manipulate the agent's analysis. SAGE's `RULES.md` limits what the agent is allowed to do, but users should be aware of this risk when running SAGE against untrusted third-party repos.
- **arXiv API rate limiting**: Sending too many queries too quickly can result in temporary IP blocks from the arXiv API. SAGE limits itself to ≤15 queries per pipeline run with a 1-second delay between calls.

### Dependency Security
- `gitnexus@1.5.3` is pinned by version. Verify the package integrity if you are running in a sensitive environment.
- Python dependencies are declared in `pyproject.toml`. Run `uv lock --check` to verify the lockfile is up to date.

---

## HuggingFace Space Security

The public demo at `huggingface.co/spaces/guglxni/SAGE-GitAgent-Demo` is a shared environment. Do not enter sensitive API keys into the public Space. Use your own private deployment for sensitive codebases.
