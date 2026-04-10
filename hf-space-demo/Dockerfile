FROM python:3.12-slim

# Install git, required build tools, and NodeJS
RUN apt-get update && apt-get install -y git curl build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install uv 
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
ENV PATH="/usr/local/bin:${PATH}"

# Configure working directory
WORKDIR /app
COPY . /app

# Install gitclaw globally
RUN npm install -g gitclaw

# Force uv to use the system Python environment inside Docker
ENV UV_SYSTEM_PYTHON=1

# Install SAGE python tools and streamlit
RUN uv sync --all-groups
RUN uv pip install -e . streamlit

# Expose Streamlit default port
EXPOSE 7860

# Run the Streamlit app correctly exposing to HF router on 0.0.0.0
CMD ["streamlit", "run", "hf-space-demo/app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
