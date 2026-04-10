# SAGE HuggingFace Space — Docker build
# Build context: SAGE repo root (COPY . /app gets all agent files)
# HuggingFace Spaces: Dockerfile must be at repo root, app_port: 7860

FROM python:3.12-slim

# ── System dependencies ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    git curl build-essential ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── uv (fast Python package manager) ──────────────────────────────────────
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
ENV PATH="/usr/local/bin:${PATH}"

# ── Copy SAGE agent source ─────────────────────────────────────────────────
WORKDIR /app
COPY . /app

# ── Node.js tools ──────────────────────────────────────────────────────────
# Install gitclaw globally so `gitclaw` binary is on PATH
RUN npm install -g gitclaw

# Pre-cache gitnexus@1.5.3 so npx doesn't download it at runtime per request
# (|| true: don't fail build if --version flag not supported)
RUN npx -y gitnexus@1.5.3 --version 2>/dev/null || \
    npx -y gitnexus@1.5.3 --help 2>/dev/null || true

# ── Python dependencies ────────────────────────────────────────────────────
ENV UV_SYSTEM_PYTHON=1

# Install project deps from pyproject.toml (includes litellm, httpx, uvicorn)
RUN uv sync --all-groups 2>/dev/null || true

# Install SAGE package + Streamlit
RUN uv pip install -e . streamlit

# ── HuggingFace Spaces runs as uid 1000 ───────────────────────────────────
# /tmp is writable by all users — session dirs live there.
# Verify the agent files are readable at build time.
RUN ls /app/agent.yaml /app/SOUL.md /app/RULES.md /app/skills /app/tools /app/src \
    && echo "SAGE agent files verified."

# ── Runtime ───────────────────────────────────────────────────────────────
EXPOSE 7860
CMD ["streamlit", "run", "hf-space-demo/app.py", \
     "--server.port", "7860", \
     "--server.address", "0.0.0.0", \
     "--server.headless", "true", \
     "--browser.gatherUsageStats", "false"]
