# SAGE HuggingFace Space — standalone Docker build
# Build context: hf-space-demo/ directory (COPY . /app gets all agent files)
# HuggingFace Spaces: Dockerfile at repo root, app_port: 7860

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
RUN npm install -g gitclaw

# Pre-cache gitnexus@1.5.3 so npx doesn't download it at runtime per request
RUN npx -y gitnexus@1.5.3 --version 2>/dev/null || \
    npx -y gitnexus@1.5.3 --help 2>/dev/null || true

# ── Python dependencies ────────────────────────────────────────────────────
ENV UV_SYSTEM_PYTHON=1
RUN uv pip install streamlit

# ── Verify agent files ─────────────────────────────────────────────────────
RUN ls /app/agent.yaml /app/SOUL.md /app/RULES.md /app/tools /app/src \
    && echo "SAGE agent files verified."

# ── Runtime ───────────────────────────────────────────────────────────────
EXPOSE 7860
CMD ["streamlit", "run", "app.py", \
     "--server.port", "7860", \
     "--server.address", "0.0.0.0", \
     "--server.headless", "true", \
     "--browser.gatherUsageStats", "false"]
