# ─────────────────────────────────────────────────────────────────────────────
# Agentic RAG Memory Engine — Docker Image
# github.com/mhndayesh/infinite-context-rag
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ┌─ Optional: change the working directory inside the container ───────────┐
# │  All files will live at /app. Memory DB is mounted as a volume.        │
# └────────────────────────────────────────────────────────────────────────┘
WORKDIR /app

# Install system dependencies (needed by chromadb / sqlite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the engine and examples
COPY memory_engine.py .
COPY example_chat.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# ┌─ Environment variables (override in docker-compose.yml or .env) ────────┐
# │  OLLAMA_URL — point to your Ollama instance                            │
# │  LLM_MODEL  — model to use (must be pulled in Ollama first)           │
# │  DB_PATH    — where memory is stored (mounted as a volume below)      │
# └────────────────────────────────────────────────────────────────────────┘
ENV OLLAMA_URL="http://ollama:11434"
ENV LLM_MODEL="phi4-mini:3.8b"
ENV EMBED_MODEL="nomic-embed-text"
ENV DB_PATH="/app/memory_db"
ENV NUM_CTX="4096"

# Expose nothing — this is a library/CLI, not a web server.
# If you wrap it in FastAPI, expose the port here:
# EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
