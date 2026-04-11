"""SAGE — ML Research Intelligence Agent: HuggingFace Space Demo.

Architecture:
  - Each user session gets two isolated temp dirs:
      session_dir: SAGE agent files + where gitclaw writes reports (--dir)
      clone_dir:   target repo + where gitnexus runs analyze (cwd)
  - Provider keys are passed directly via env vars — no LiteLLM proxy.
  - Custom providers use GITCLAW_MODEL_BASE_URL (not OPENAI_BASE_URL).
  - gitnexus@1.5.3 is pre-cached in the Docker image.

Pipeline (3 sequential --prompt calls, pre-fetched data):
  We pre-fetch ALL external data in Python before any gitclaw call:
    Step 1 → TECHNIQUES.md:
      gitnexus queries run in Python → JSON parsed to bullet text → injected.
      Model only needs to call write(TECHNIQUES.md).
    Step 2 → PAPERS.md:
      arXiv API called directly in Python → XML parsed to paper list → injected.
      Model only needs to call write(PAPERS.md).
    Step 3 → GAPS.md:
      Both files injected as context.
      Model only needs to call write(GAPS.md).

  Pre-fetching eliminates:
    - Tool call failures (network errors inside gitclaw session)
    - Large XML responses exhausting model context
    - Models outputting analysis as text instead of write() calls
    - Hallucinated file paths from raw JSON
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import streamlit as st

# ── Constants ─────────────────────────────────────────────────────────────────
STEP_TIMEOUT = 150  # seconds per step (3 steps × 150s = 450s max total)

SAGE_AGENT_FILES = ["agent.yaml", "DUTIES.md", "AGENTS.md"]
# All agent files live alongside app.py — works both locally and on HF Space
SAGE_DEMO_ROOT = Path(__file__).parent
SAGE_APP_ROOT = SAGE_DEMO_ROOT  # agent.yaml, tools/, src/ are in the same dir as app.py
SAGE_AGENT_DIRS = ["tools", "src", "knowledge"]  # no skills — prevents SKILL MATCH hooks hijacking prompts

# Provider configurations — model strings match pi-ai's registry exactly.
PROVIDERS: dict[str, dict] = {
    "Groq": {
        "env_key": "GROQ_API_KEY",
        "gitclaw_prefix": "groq",
        "models": {
            "Llama 4 Scout 17B (fast, recommended)": "meta-llama/llama-4-scout-17b-16e-instruct",
            "Llama 4 Maverick 17B (large context)": "meta-llama/llama-4-maverick-17b-128e-instruct",
            "Llama 3.3 70B Versatile": "llama-3.3-70b-versatile",
            "Llama 3.1 8B Instant (fastest)": "llama-3.1-8b-instant",
            "Kimi K2 (Moonshot)": "moonshotai/kimi-k2-instruct",
        },
        "key_url": "https://console.groq.com/keys",
        "key_hint": "gsk_...",
        "needs_base_url": False,
    },
    "OpenAI": {
        "env_key": "OPENAI_API_KEY",
        "gitclaw_prefix": "openai",
        "models": {
            "GPT-4o": "gpt-4o",
            "GPT-4o Mini": "gpt-4o-mini",
            "o1": "o1",
            "o3-mini": "o3-mini",
        },
        "key_url": "https://platform.openai.com/api-keys",
        "key_hint": "sk-...",
        "needs_base_url": False,
    },
    "Anthropic": {
        "env_key": "ANTHROPIC_API_KEY",
        "gitclaw_prefix": "anthropic",
        "models": {
            "Claude Sonnet 4.6": "claude-sonnet-4-6",
            "Claude Haiku 4.5": "claude-haiku-4-5-20251001",
            "Claude Opus 4.6": "claude-opus-4-6",
        },
        "key_url": "https://console.anthropic.com/",
        "key_hint": "sk-ant-...",
        "needs_base_url": False,
    },
    "Custom / OpenAI-Compatible": {
        "env_key": "OPENAI_API_KEY",
        "gitclaw_prefix": "openai",
        "models": {},
        "key_url": None,
        "key_hint": "your-api-key",
        "needs_base_url": True,
    },
}

# ── Session Management ────────────────────────────────────────────────────────

class SAGESession:
    """Isolated per-user session with dedicated temp directories."""

    def __init__(self) -> None:
        self.session_id = uuid.uuid4().hex[:12]
        self.session_dir = Path(f"/tmp/sage-session-{self.session_id}")
        self.clone_dir: Path | None = None
        self.repo_name: str = ""

    def setup(self) -> None:
        """Copy SAGE agent files into the isolated session directory.

        Uses simplified SOUL.md + RULES.md from hf-space-demo/ so the agent
        isn't blocked by the full SAGE rules (fetch-abstract mandates, paper-verifier
        delegation, domain restrictions) that prevent demo-speed operation.
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)
        # Copy simplified soul/rules from demo dir first
        for fname in ["SOUL.md", "RULES.md"]:
            src = SAGE_DEMO_ROOT / fname
            if src.exists():
                shutil.copy2(src, self.session_dir / fname)
        # Copy remaining agent definition files from app root
        for fname in SAGE_AGENT_FILES:
            src = SAGE_APP_ROOT / fname
            if src.exists():
                shutil.copy2(src, self.session_dir / fname)
        # Copy tools + knowledge (no skills — avoids SKILL MATCH hook hijacking)
        for dname in SAGE_AGENT_DIRS:
            src = SAGE_APP_ROOT / dname
            dst = self.session_dir / dname
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

        # Pre-initialize git repo so gitclaw skips its own init+commit flow,
        # which would fail if global commit.gpgsign=true requires a passphrase.
        _run = lambda *args: subprocess.run(
            args, cwd=str(self.session_dir), capture_output=True
        )
        _run("git", "init")
        _run("git", "config", "commit.gpgsign", "false")
        _run("git", "config", "user.email", "sage@localhost")
        _run("git", "config", "user.name", "SAGE")
        _run("git", "add", "-A")
        _run("git", "commit", "--allow-empty", "-m", "sage: session init")

    def setup_clone_dir(self, repo_url: str) -> Path:
        """Prepare a named clone directory — basename becomes the gitnexus repo name."""
        # Use repo name as subdirectory so gitnexus sees a clean repo name.
        self.repo_name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
        clone_base = Path(f"/tmp/sage-target-{self.session_id}")
        clone_base.mkdir(parents=True, exist_ok=True)
        self.clone_dir = clone_base / self.repo_name  # /tmp/sage-target-xxx/minGPT
        return self.clone_dir

    def read_report(self, filename: str) -> str | None:
        path = self.session_dir / filename
        return path.read_text(encoding="utf-8") if path.exists() else None

    def cleanup(self) -> None:
        shutil.rmtree(self.session_dir, ignore_errors=True)
        if self.clone_dir:
            shutil.rmtree(self.clone_dir.parent, ignore_errors=True)


# ── Provider Env Builder ──────────────────────────────────────────────────────

def build_provider_env(
    provider: str,
    api_key: str,
    model_id: str,
    base_url: str | None = None,
) -> tuple[dict[str, str], str]:
    """Returns (env_dict, gitclaw_model_string).

    Clears all provider keys first to prevent cross-contamination between calls.
    """
    config = PROVIDERS[provider]
    env = os.environ.copy()

    # Clear all provider-specific keys
    for p in PROVIDERS.values():
        env.pop(p["env_key"], None)
    env.pop("GITCLAW_MODEL_BASE_URL", None)

    # Set the correct key
    env[config["env_key"]] = api_key

    if provider == "Custom / OpenAI-Compatible":
        if base_url:
            # GITCLAW_MODEL_BASE_URL is the correct env var — not OPENAI_BASE_URL
            env["GITCLAW_MODEL_BASE_URL"] = base_url.rstrip("/")
        gitclaw_model = f"openai:{model_id}"
    else:
        gitclaw_model = f"{config['gitclaw_prefix']}:{model_id}"

    return env, gitclaw_model


# ── Prompt Templates ──────────────────────────────────────────────────────────

def build_step1_prompt(repo_name: str, gitnexus_json: str) -> str:
    """Step 1: Write TECHNIQUES.md from pre-fetched gitnexus AST data.

    We inject the raw gitnexus JSON directly so the model writes real file:line
    references instead of hallucinating paths.
    """
    return (
        f"You are SAGE, an ML research intelligence agent.\n\n"
        f"Here is the AST knowledge graph data for the '{repo_name}' codebase "
        f"(queried via gitnexus):\n\n{gitnexus_json}\n\n"
        f"Write TECHNIQUES.md with two sections:\n"
        f"1. ## Detected Techniques — for each technique found in the data above, "
        f"list: technique name, exact file:line from the data, brief description.\n"
        f"2. ## Notable Absences — standard ML patterns for this architecture type "
        f"that are NOT present in the data above (these are the highest-value gaps).\n\n"
        f"Call write(path=\"TECHNIQUES.md\") with this content."
    )


def build_step2_prompt(repo_name: str, papers_text: str) -> str:
    """Step 2: arXiv papers pre-fetched in Python, model only writes PAPERS.md."""
    return (
        f"Call write(path=\"PAPERS.md\") with a markdown file listing these arXiv papers "
        f"relevant to the '{repo_name}' ML codebase.\n\n"
        f"The papers were retrieved from the arXiv API:\n\n{papers_text}\n\n"
        f"Format PAPERS.md with:\n"
        f"## High Relevance Papers\n"
        f"(architecture/training papers — title, arxiv:ID, year, one sentence on relevance)\n\n"
        f"## Gap Papers\n"
        f"(papers for techniques NOT found in the codebase — explain the gap)\n\n"
        f"Call write(path=\"PAPERS.md\") now. Do not output text."
    )


def build_step3_prompt(repo_name: str, techniques_md: str, papers_md: str) -> str:
    """Step 3: Cross-reference TECHNIQUES.md + PAPERS.md to write GAPS.md.

    Prompt is structured as a direct file-write command to prevent the model
    from outputting analysis as text instead of calling write().
    """
    return (
        f"Call write(path=\"GAPS.md\") with a detailed markdown gap analysis for '{repo_name}'.\n\n"
        f"Use this exact structure:\n\n"
        f"## Summary\n"
        f"X techniques detected in {repo_name}, Y papers cross-referenced, Z gaps identified.\n\n"
        f"## Critical Gaps\n"
        f"For each gap write: **Gap name** (Severity: Critical/Improvement/Experimental)\n"
        f"- Current: what the code does now, with file:line reference\n"
        f"- SOTA: what the paper recommends (arxiv:ID — paper title)\n"
        f"- Impact: one sentence on the performance/quality benefit\n\n"
        f"## Improvement Opportunities\n"
        f"For each opportunity: **Technique name** — how it can be upgraded based on arxiv:ID\n\n"
        f"## Experimental Suggestions\n"
        f"For each suggestion: **Missing technique** (arxiv:ID) — 2 sentences on expected benefit\n\n"
        f"---\n"
        f"DATA — TECHNIQUES.md:\n{techniques_md}\n\n"
        f"DATA — PAPERS.md:\n{papers_md}\n\n"
        f"Now call write(path=\"GAPS.md\") immediately with the complete gap analysis. "
        f"Do not output text — only call the write tool."
    )


# ── Pipeline Execution ────────────────────────────────────────────────────────

def clone_repo(repo_url: str, clone_dir: Path, status_fn) -> None:
    status_fn(f"Cloning `{repo_url}` (shallow)...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Clone failed: {result.stderr[:300]}")


def _gitnexus_json_to_text(query: str, raw_json: str) -> str:
    """Convert gitnexus JSON output to a clean markdown-friendly text block.

    The raw JSON confuses models into writing JSON instead of markdown.
    We convert to readable bullet-point text so models produce correct output.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return f"Query: {query}\n  (unparseable output)"

    lines = [f"Query: {query}"]

    # Definitions: classes, functions, files with file paths and line numbers
    for defn in data.get("definitions", [])[:15]:
        name = defn.get("name", "?")
        file_path = defn.get("filePath", "?")
        start = defn.get("startLine")
        end = defn.get("endLine")
        module = defn.get("module", "")
        loc = f":{start}" if start else ""
        if end and end != start:
            loc = f":{start}-{end}"
        mod_tag = f" [{module}]" if module else ""
        lines.append(f"  - {name} ({file_path}{loc}){mod_tag}")

    # Process symbols with execution flow info
    for sym in data.get("process_symbols", [])[:8]:
        name = sym.get("name", "?")
        file_path = sym.get("filePath", "?")
        start = sym.get("startLine", "")
        end = sym.get("endLine", "")
        loc = f":{start}-{end}" if start and end else f":{start}" if start else ""
        lines.append(f"  - {name} ({file_path}{loc}) [execution flow]")

    if len(lines) == 1:
        lines.append("  (no matching symbols found)")

    return "\n".join(lines)


def run_gitnexus_queries_local(repo_name: str, status_fn) -> str:
    """Run 3 gitnexus queries in Python and return clean human-readable text.

    Runs from any cwd — gitnexus uses its global registry keyed by repo name.
    Returns formatted text (not raw JSON) ready to inject into the Step 1 prompt.
    """
    queries = [
        "transformer model classes attention architecture",
        "optimizer training loop loss function",
        "positional encoding embedding layers normalization",
    ]
    parts = []
    for q in queries:
        try:
            result = subprocess.run(
                ["npx", "-y", "gitnexus@1.5.3", "query", q, "--repo", repo_name],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts.append(_gitnexus_json_to_text(q, result.stdout))
            else:
                parts.append(f"Query: {q}\n  (no results)")
        except Exception as e:
            parts.append(f"Query: {q}\n  (error: {e})")
    combined = "\n\n".join(parts)
    status_fn(f"AST queries complete ({len(parts)} queries, {len(combined)} chars).")
    return combined


def _parse_arxiv_xml(xml_text: str) -> list[dict]:
    """Parse arXiv Atom XML into a list of paper dicts.

    Returns list of {title, arxiv_id, year, summary} dicts.
    """
    papers = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            id_el = entry.find("atom:id", ns)
            published_el = entry.find("atom:published", ns)
            summary_el = entry.find("atom:summary", ns)

            if title_el is None or id_el is None:
                continue

            full_id = id_el.text or ""
            # Extract short arxiv ID from URL like https://arxiv.org/abs/2301.12345
            arxiv_id = full_id.split("/abs/")[-1].strip()
            year = (published_el.text or "")[:4] if published_el is not None else "?"
            summary = (summary_el.text or "").strip()[:200] if summary_el is not None else ""
            title = (title_el.text or "").strip().replace("\n", " ")

            papers.append({
                "title": title,
                "arxiv_id": arxiv_id,
                "year": year,
                "summary": summary,
            })
    except ET.ParseError:
        pass
    return papers


def _fetch_arxiv(query: str, max_results: int = 4) -> list[dict]:
    """Fetch papers from arXiv API for a single query using httpx."""
    encoded = urllib.parse.quote_plus(query)
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=all:{encoded}"
        f"&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )
    try:
        import httpx
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return _parse_arxiv_xml(resp.text)
    except ImportError:
        # Fallback to urllib if httpx not available
        import urllib.request
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return _parse_arxiv_xml(resp.read().decode("utf-8"))
        except Exception:
            return []
    except Exception:
        return []


def run_arxiv_searches_local(techniques_md: str, repo_name: str, status_fn) -> str:
    """Run 3 arXiv searches in Python based on TECHNIQUES.md content.

    Extracts search terms from TECHNIQUES.md and returns formatted paper list.
    Pre-fetching in Python avoids large XML responses inside gitclaw sessions
    that exhaust model context or cause tool call failures.
    """
    # Extract search queries from TECHNIQUES.md using simple heuristics
    lines = techniques_md.lower()

    # Query 1: architecture type
    if "transformer" in lines or "attention" in lines:
        q1 = f"transformer attention mechanism {repo_name} architecture"
    elif "cnn" in lines or "convolution" in lines:
        q1 = "convolutional neural network architecture training"
    elif "diffusion" in lines:
        q1 = "diffusion model generative training"
    else:
        q1 = f"deep learning neural network architecture {repo_name}"

    # Query 2: training / optimizer
    if "adamw" in lines:
        q2 = "AdamW optimizer transformer training convergence"
    elif "adam" in lines:
        q2 = "Adam optimizer deep learning training"
    elif "training loop" in lines or "loss" in lines:
        q2 = "transformer training optimization techniques"
    else:
        q2 = "neural network training optimizer learning rate"

    # Query 3: first notable absence
    q3 = "transformer gradient clipping learning rate scheduler"
    for line in techniques_md.splitlines():
        if line.strip().startswith(("- ", "* ", "1.", "2.", "3.")):
            absence_text = re.sub(r"^[-*\d.]\s*\*?\*?", "", line).strip().rstrip("*")
            if absence_text and len(absence_text) > 5:
                q3 = f"{absence_text} transformer deep learning"
                break

    all_papers: list[dict] = []
    seen_ids: set[str] = set()
    query_labels = ["architecture", "training/optimizer", "notable-absence"]

    for label, query in zip(query_labels, [q1, q2, q3]):
        status_fn(f"Searching arXiv: {query[:60]}...")
        papers = _fetch_arxiv(query, max_results=3)
        for p in papers:
            if p["arxiv_id"] not in seen_ids:
                seen_ids.add(p["arxiv_id"])
                p["label"] = label
                all_papers.append(p)

    if not all_papers:
        return "(no arXiv papers found)"

    lines_out = []
    for p in all_papers:
        lines_out.append(
            f"- [{p['label']}] **{p['title']}** "
            f"(arxiv:{p['arxiv_id']}, {p['year']}) — {p['summary'][:150]}"
        )
    status_fn(f"arXiv: {len(all_papers)} papers found across 3 queries.")
    return "\n".join(lines_out)


def run_gitnexus_analyze(clone_dir: Path, status_fn) -> None:
    status_fn(f"Indexing AST with gitnexus@1.5.3...")
    result = subprocess.run(
        ["npx", "-y", "gitnexus@1.5.3", "analyze"],
        cwd=str(clone_dir),
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        # Non-fatal: SAGE will still work, just without AST data
        status_fn(f"⚠️ gitnexus analyze warning: {result.stderr[:150]}")
    else:
        # Parse summary from output
        for line in result.stdout.splitlines():
            if "nodes" in line or "indexed" in line.lower():
                status_fn(f"AST indexed: {line.strip()}")
                break


def _run_gitclaw_step(
    session_dir: Path,
    env: dict,
    model: str,
    prompt: str,
    step_label: str,
    log_fn,
    full_log_ref: list,
) -> int:
    """Run one gitclaw --prompt invocation (single-turn) and stream its output.

    gitclaw --prompt exits automatically after one LLM turn + tool calls.
    The prompt is passed via --prompt flag (no stdin/REPL issues).
    """
    cmd = [
        "gitclaw",
        "--dir", str(session_dir),
        "-m", model,
        "--prompt", prompt,
    ]
    process = subprocess.Popen(
        cmd,
        cwd=str(session_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        bufsize=1,
    )

    def _read() -> None:
        for line in iter(process.stdout.readline, ""):
            full_log_ref[0] += line
            log_fn(f"[{step_label}]\n" + full_log_ref[0])
        process.stdout.close()

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()

    try:
        process.wait(timeout=STEP_TIMEOUT)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=10)

    reader.join(timeout=5)
    return process.returncode


def _synthesize_gaps_fallback(repo_name: str, techniques_md: str, papers_md: str) -> str:
    """Build a basic GAPS.md from the pre-fetched data without an LLM call.

    Used when the model fails to write GAPS.md. Extracts notable absences from
    TECHNIQUES.md and matches them against papers in PAPERS.md.
    """
    # Count techniques and papers for summary
    techniques_count = techniques_md.count("\n- ") + techniques_md.count("\n**")
    papers_count = papers_md.count("arxiv:")

    # Extract notable absences from TECHNIQUES.md
    absences: list[str] = []
    in_absences = False
    for line in techniques_md.splitlines():
        if "notable absence" in line.lower() or "## notable" in line.lower():
            in_absences = True
            continue
        if in_absences and line.startswith("##"):
            break
        if in_absences and line.strip().startswith(("-", "*", "1", "2", "3", "4", "5")):
            absence = re.sub(r"^[-*\d.]\s*\*?\*?", "", line).split("—")[0].strip().rstrip("*")
            if absence:
                absences.append(absence)

    # Extract paper references from PAPERS.md
    paper_refs: list[str] = []
    for line in papers_md.splitlines():
        if "arxiv:" in line.lower():
            paper_refs.append(line.strip())

    lines = [
        f"# Gap Analysis: {repo_name}",
        "",
        "## Summary",
        f"{techniques_count} techniques detected, {papers_count} papers cross-referenced, "
        f"{len(absences)} gaps identified from notable absences.",
        "",
        "## Critical Gaps",
    ]

    if absences and paper_refs:
        for i, absence in enumerate(absences[:5]):
            paper_ref = paper_refs[i % len(paper_refs)] if paper_refs else "(see PAPERS.md)"
            lines.append(f"**{absence}** (Severity: Improvement)")
            lines.append(f"- Current: Not implemented in {repo_name}")
            lines.append(f"- SOTA: {paper_ref}")
            lines.append(f"- Impact: Adding {absence.lower()} could improve model performance.")
            lines.append("")
    else:
        lines.append("See TECHNIQUES.md Notable Absences and PAPERS.md for details.")
        lines.append("")

    lines += [
        "## Improvement Opportunities",
        "Review PAPERS.md High Relevance Papers for upgrade paths for detected techniques.",
        "",
        "## Experimental Suggestions",
        "Implement the Notable Absences listed in TECHNIQUES.md.",
        "See PAPERS.md Gap Papers for relevant research with implementation guidance.",
    ]

    return "\n".join(lines)


def run_sage_pipeline(
    session: "SAGESession",
    env: dict,
    model: str,
    log_fn,
) -> tuple[int, str]:
    """Run the 3-step SAGE pipeline using sequential gitclaw --prompt calls.

    All external data is pre-fetched in Python before any gitclaw call:
    Step 1 — TECHNIQUES.md: gitnexus queries run in Python → formatted text injected.
    Step 2 — PAPERS.md: arXiv API called in Python → paper list injected.
    Step 3 — GAPS.md: both files injected as context.

    Each step's model only needs to call write() once — no tool failures possible.
    Fallbacks ensure all 3 files are always written even if the model produces
    text instead of a tool call.
    """
    full_log = [""]  # mutable container for thread-safe accumulation

    # ── Step 1: AST scan — fetch gitnexus data in Python, write TECHNIQUES.md ─
    log_fn("[Step 1/3] Fetching AST data from gitnexus...")
    gitnexus_data = run_gitnexus_queries_local(session.repo_name, log_fn)
    step1_prompt = build_step1_prompt(session.repo_name, gitnexus_data)
    _run_gitclaw_step(
        session.session_dir, env, model, step1_prompt,
        "Step 1: TECHNIQUES.md", log_fn, full_log,
    )

    techniques_path = session.session_dir / "TECHNIQUES.md"
    techniques_md = techniques_path.read_text(encoding="utf-8") if techniques_path.exists() else ""
    if not techniques_md:
        # Fallback: synthesize TECHNIQUES.md from raw gitnexus data
        techniques_md = f"# Techniques in {session.repo_name}\n\n{gitnexus_data[:3000]}"
        techniques_path.write_text(techniques_md, encoding="utf-8")
        log_fn(full_log[0] + "\n⚠️ TECHNIQUES.md not written by model — using raw AST data.")

    # ── Step 2: arXiv papers — pre-fetch in Python, model only writes PAPERS.md ─
    log_fn(full_log[0] + f"\n[Step 2/3] Fetching arXiv papers...")
    papers_text = run_arxiv_searches_local(techniques_md, session.repo_name, log_fn)
    step2_prompt = build_step2_prompt(session.repo_name, papers_text)
    _run_gitclaw_step(
        session.session_dir, env, model, step2_prompt,
        "Step 2: PAPERS.md", log_fn, full_log,
    )

    papers_path = session.session_dir / "PAPERS.md"
    papers_md = papers_path.read_text(encoding="utf-8") if papers_path.exists() else ""
    if not papers_md:
        # Fallback: write PAPERS.md directly from pre-fetched data
        papers_md = f"# Papers\n\n{papers_text}"
        papers_path.write_text(papers_md, encoding="utf-8")
        log_fn(full_log[0] + "\n⚠️ PAPERS.md not written by model — using pre-fetched data.")

    # ── Step 3: Gap analysis — inject both files, write GAPS.md ──────────────
    log_fn(full_log[0] + f"\n[Step 3/3] Writing gap analysis...")
    step3_prompt = build_step3_prompt(
        session.repo_name, techniques_md[:3000], papers_md[:3000]
    )
    rc = _run_gitclaw_step(
        session.session_dir, env, model, step3_prompt,
        "Step 3: GAPS.md", log_fn, full_log,
    )

    gaps_path = session.session_dir / "GAPS.md"
    if not gaps_path.exists():
        # Fallback: synthesize GAPS.md from pre-fetched data without LLM
        gaps_md = _synthesize_gaps_fallback(session.repo_name, techniques_md, papers_md)
        gaps_path.write_text(gaps_md, encoding="utf-8")
        log_fn(full_log[0] + "\n⚠️ GAPS.md not written by model — using synthesized fallback.")

    return rc, full_log[0]


def collect_reports(session: SAGESession) -> dict[str, str]:
    """Read generated report files from the session dir."""
    report_files = {
        "TECHNIQUES": "TECHNIQUES.md",
        "PAPERS": "PAPERS.md",
        "GAPS": "GAPS.md",
        "SUMMARIES": "SUMMARIES.md",
        "RELATED WORK": "RELATED_WORK.md",
    }
    return {
        label: content
        for label, fname in report_files.items()
        if (content := session.read_report(fname)) is not None
    }


# ── Streamlit UI ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SAGE — ML Research Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Header
st.title("🧠 SAGE: ML Research Intelligence Agent")
st.markdown(
    "Analyze any ML codebase against the latest arXiv papers. "
    "SAGE scans your code AST, hunts relevant research, and identifies improvement opportunities — "
    "outputting **TECHNIQUES.md**, **PAPERS.md**, and **GAPS.md** reports."
)
st.divider()

# ── LLM Configuration ─────────────────────────────────────────────────────────
with st.expander("⚙️ LLM Configuration", expanded=True):
    col_provider, col_model, col_key = st.columns([1, 2, 2])

    with col_provider:
        provider = st.selectbox(
            "Provider",
            options=list(PROVIDERS.keys()),
            index=0,
            help="Groq is free-tier and verified working out of the box.",
        )

    provider_cfg = PROVIDERS[provider]
    is_custom = provider == "Custom / OpenAI-Compatible"

    with col_model:
        if is_custom:
            custom_model_id = st.text_input(
                "Model name",
                placeholder="e.g. mistral-7b-instruct, llama-3.1-70b",
                help="The model name as your endpoint expects it.",
            )
            custom_base_url = st.text_input(
                "Base URL",
                placeholder="https://api.your-provider.com/v1",
                help="OpenAI-compatible base URL. Used via GITCLAW_MODEL_BASE_URL.",
            )
        else:
            model_display = st.selectbox(
                "Model",
                options=list(provider_cfg["models"].keys()),
                index=0,
            )

    with col_key:
        key_help = (
            f"Get a key at {provider_cfg['key_url']}"
            if provider_cfg.get("key_url") else
            "Your API key for the custom endpoint."
        )
        api_key = st.text_input(
            "API Key (BYOK)",
            type="password",
            placeholder=provider_cfg["key_hint"],
            help=key_help + " Never logged or stored — passed only via env var.",
        )

# ── Repository Input ──────────────────────────────────────────────────────────
repo_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/karpathy/minGPT",
    help="Must be a public repository. Cloned with --depth 1 (no history).",
)

# ── Run Button ────────────────────────────────────────────────────────────────
run_col, _ = st.columns([1, 4])
with run_col:
    run_clicked = st.button("🔬 Run SAGE Analysis", type="primary", use_container_width=True)

if run_clicked:
    # Input validation
    errors = []
    if not repo_url or "github.com" not in repo_url:
        errors.append("Enter a valid GitHub repository URL.")
    if not api_key:
        errors.append("Enter an API key.")
    if is_custom:
        if not custom_model_id:
            errors.append("Enter a model name for the custom provider.")
        if not custom_base_url:
            errors.append("Enter a base URL for the custom provider.")

    for err in errors:
        st.error(err)

    if not errors:
        # Resolve model id and build env
        if is_custom:
            model_id = custom_model_id
            base_url = custom_base_url
        else:
            model_id = provider_cfg["models"][model_display]
            base_url = None

        env, gitclaw_model = build_provider_env(provider, api_key, model_id, base_url)

        session = SAGESession()
        try:
            # ── Phase 1: Setup & Clone ────────────────────────────────────
            with st.status("Preparing analysis environment...", expanded=True) as status_box:
                st.write(f"Session `{session.session_id}` created.")
                session.setup()

                clone_dir = session.setup_clone_dir(repo_url)
                clone_repo(repo_url, clone_dir, st.write)
                st.write(f"Cloned to `{clone_dir.name}/`")

                run_gitnexus_analyze(clone_dir, st.write)
                st.write(f"Provider: **{provider}** | Model: `{gitclaw_model}`")
                status_box.update(label="Environment ready. Starting SAGE pipeline...", state="running")

            # ── Phase 2: Run Pipeline ─────────────────────────────────────
            st.subheader("📡 Live Agent Output")
            log_container = st.empty()

            def update_log(full_log: str) -> None:
                # Show last 4000 chars to keep the UI responsive
                display = full_log[-4000:] if len(full_log) > 4000 else full_log
                log_container.code(display, language=None)

            with st.spinner("SAGE pipeline running — scan → papers → gaps (up to ~3 min)..."):
                returncode, full_log = run_sage_pipeline(session, env, gitclaw_model, update_log)

            # ── Phase 3: Display Reports ──────────────────────────────────
            reports = collect_reports(session)

            if not reports:
                st.error(
                    "The pipeline ran but no report files were generated. "
                    "This usually means the API key was rejected or the model hit a rate limit. "
                    "Check the live output above for error details."
                )
            else:
                st.success(
                    f"✅ Analysis complete — **{len(reports)}** report(s) generated: "
                    + ", ".join(f"`{k}.md`" for k in reports)
                )
                st.subheader("📄 Analysis Reports")

                tabs = st.tabs([f"📋 {label}" for label in reports])
                for tab, (label, content) in zip(tabs, reports.items()):
                    with tab:
                        dl_col, _ = st.columns([1, 4])
                        with dl_col:
                            st.download_button(
                                label=f"⬇️ Download {label}.md",
                                data=content,
                                file_name=f"{label.replace(' ', '_')}.md",
                                mime="text/markdown",
                                key=f"dl_{label}_{session.session_id}",
                            )
                        if label == "RELATED WORK":
                            st.code(content, language="latex")
                        else:
                            st.markdown(content)

        except RuntimeError as e:
            st.error(f"**Error:** {e}")
        except subprocess.TimeoutExpired:
            st.error(
                f"⏱️ A pipeline step timed out (limit: {STEP_TIMEOUT}s per step). "
                "Try a smaller repository or a faster model (Llama 3.1 8B Instant)."
            )
        except Exception as e:
            st.error(f"Unexpected error: `{type(e).__name__}: {e}`")
        finally:
            session.cleanup()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("About SAGE")
    st.markdown("""
**SAGE** (Search, Analyze, Gap-detect, Explain) is a [GitAgent](https://github.com/open-gitagent/gitagent)-standard ML research intelligence agent.

**Pipeline:**
1. `scan-codebase` — AST analysis via gitnexus
2. `hunt-papers` — arXiv paper discovery
3. `identify-gaps` — gap analysis with citations

**Output files:**
- `TECHNIQUES.md` — detected ML techniques
- `PAPERS.md` — relevant arXiv papers
- `GAPS.md` — research gaps with citations

**Supported providers:**
- **Groq** — free tier, fast inference
- **OpenAI** — GPT-4o family
- **Anthropic** — Claude family
- **Custom** — any OpenAI-compatible endpoint

**Source code:** [guglxni/SAGE-GitAgent](https://github.com/guglxni/SAGE-GitAgent)
    """)

    st.divider()
    st.caption("API keys are never logged or stored. Each analysis runs in an isolated temporary session that is deleted after completion.")
