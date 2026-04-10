"""SAGE — ML Research Intelligence Agent: HuggingFace Space Demo.

Architecture:
  - Each user session gets two isolated temp dirs:
      session_dir: SAGE agent files + where gitclaw writes reports (--dir)
      clone_dir:   target repo + where gitnexus runs analyze (cwd)
  - Provider keys are passed directly via env vars — no LiteLLM proxy.
  - Custom providers use GITCLAW_MODEL_BASE_URL (not OPENAI_BASE_URL).
  - gitnexus@1.5.3 is pre-cached in the Docker image.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import streamlit as st

# ── Constants ─────────────────────────────────────────────────────────────────
SAGE_APP_ROOT = Path("/app")
SESSION_TIMEOUT = 300  # seconds

SAGE_AGENT_FILES = ["agent.yaml", "SOUL.md", "RULES.md", "DUTIES.md", "AGENTS.md"]
SAGE_AGENT_DIRS = ["skills", "tools", "src", "knowledge", "hooks", "agents", "config"]

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
        """Copy SAGE agent files into the isolated session directory."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        for fname in SAGE_AGENT_FILES:
            src = SAGE_APP_ROOT / fname
            if src.exists():
                shutil.copy2(src, self.session_dir / fname)
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


# ── Prompt Template ───────────────────────────────────────────────────────────

def build_prompt(repo_name: str) -> str:
    return f"""Analyze the ML codebase '{repo_name}'. It is indexed in gitnexus as repo '{repo_name}'.

Complete EXACTLY these 3 steps IN ORDER. For EACH step, call the write tool immediately — do NOT fetch extra data after writing.

STEP 1 — SCAN (3 gitnexus queries, then write file):
Call gitnexus-query 3 times:
  1. query="optimizer training AdamW SGD" repo="{repo_name}"
  2. query="transformer attention neural network" repo="{repo_name}"
  3. query="loss function cross entropy" repo="{repo_name}"
IMMEDIATELY call write(path="TECHNIQUES.md", content="# ML Techniques in {repo_name}\\n\\n## Detected:\\n[technique — file:line — description]\\n\\n## Notable Absences:\\n[missing patterns for this architecture]")

STEP 2 — PAPERS (2 arxiv searches, then write file):
Call arxiv-search 2 times for top 2 techniques from Step 1.
IMMEDIATELY call write(path="PAPERS.md", content="# Relevant Papers for {repo_name}\\n\\n## [Technique Name]\\n- **[Title]** — arxiv:[ID]\\n  Why relevant: [one sentence]\\n...")

STEP 3 — GAPS (write file immediately, no extra tool calls):
Using ONLY what you know from Steps 1 and 2, IMMEDIATELY call:
write(path="GAPS.md", content="# Research Gaps in {repo_name}\\n\\n## Critical Gaps\\n- **[Gap Name]**: [current code vs paper recommendation] — arxiv:[ID]\\n\\n## Improvement Opportunities\\n- [concrete improvement with paper citation]")

RULES:
- Call write tool exactly 3 times (TECHNIQUES.md, PAPERS.md, GAPS.md)
- After writing each file, proceed to the NEXT step immediately
- Do NOT call fetch-abstract — use paper titles/IDs directly
- Do NOT describe what to write — call write(path=..., content=...) with actual content"""


# ── Pipeline Execution ────────────────────────────────────────────────────────

def clone_repo(repo_url: str, clone_dir: Path, status_fn) -> None:
    status_fn(f"Cloning `{repo_url}` (shallow)...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Clone failed: {result.stderr[:300]}")


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


def run_sage_pipeline(
    session: SAGESession,
    env: dict,
    model: str,
    log_fn,
) -> int:
    """Run gitclaw with --prompt flag (single-shot mode). Returns exit code."""
    prompt = build_prompt(session.repo_name)
    cmd = [
        "gitclaw",
        "--dir", str(session.session_dir),
        "-m", model,
        "--prompt", prompt,
    ]
    process = subprocess.Popen(
        cmd,
        cwd=str(session.session_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        bufsize=1,
    )
    full_log = ""
    # Stream output line by line until process exits
    for line in iter(process.stdout.readline, ""):
        full_log += line
        log_fn(full_log)
    process.stdout.close()
    process.wait(timeout=SESSION_TIMEOUT)
    return process.returncode, full_log


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

            with st.spinner("SAGE pipeline running — scan → papers → gaps..."):
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
                f"⏱️ Analysis timed out after {SESSION_TIMEOUT}s. "
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
