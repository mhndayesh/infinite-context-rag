# ─────────────────────────────────────────────────────────────────────────────
# INFINITE CONTEXT RAG — 100% RECALL DOCKERFILE
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code from the local context
COPY src/memory_engine.py .
COPY src/niah_eval.py .
COPY src/generate_niah_plot.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Default environment variables
ENV OLLAMA_URL="http://ollama:11434"
ENV LLM_MODEL="deepseek-r1:8b"
ENV EMBED_MODEL="nomic-embed-text"
ENV DB_PATH="/app/memory_db"
ENV NUM_CTX="4096"

# Volume for persistent memory
VOLUME ["/app/memory_db"]

ENTRYPOINT ["./entrypoint.sh"]
