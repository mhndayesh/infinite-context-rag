#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# entrypoint.sh — Container startup script
# Pulls required models from Ollama before starting the memory engine.
# ─────────────────────────────────────────────────────────────────────────────
set -e

OLLAMA_URL="${OLLAMA_URL:-http://ollama:11434}"
LLM_MODEL="${LLM_MODEL:-phi4-mini:3.8b}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"

echo "============================================================"
echo "  Agentic RAG Memory Engine — Starting Up"
echo "  Ollama URL : $OLLAMA_URL"
echo "  LLM Model  : $LLM_MODEL"
echo "  Embed Model: $EMBED_MODEL"
echo "  Memory DB  : $DB_PATH"
echo "============================================================"

# Wait for Ollama to be ready (it may still be loading after healthcheck passes)
echo "[*] Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if curl -sf "$OLLAMA_URL/" > /dev/null 2>&1; then
        echo "[*] Ollama is up."
        break
    fi
    echo "    Attempt $i/30..."
    sleep 2
done

# Pull the LLM model if not already present
echo "[*] Checking $LLM_MODEL..."
if ! curl -sf "$OLLAMA_URL/api/tags" | grep -q "$LLM_MODEL"; then
    echo "[*] Pulling $LLM_MODEL (this may take a few minutes on first run)..."
    curl -s -X POST "$OLLAMA_URL/api/pull" \
        -d "{\"name\": \"$LLM_MODEL\"}" \
        --no-buffer | grep -E '"status"' | tail -1
    echo "[*] $LLM_MODEL ready."
else
    echo "[*] $LLM_MODEL already cached."
fi

# Pull the embedding model if not already present
echo "[*] Checking $EMBED_MODEL..."
if ! curl -sf "$OLLAMA_URL/api/tags" | grep -q "nomic-embed-text"; then
    echo "[*] Pulling $EMBED_MODEL..."
    curl -s -X POST "$OLLAMA_URL/api/pull" \
        -d "{\"name\": \"$EMBED_MODEL\"}" \
        --no-buffer | grep -E '"status"' | tail -1
    echo "[*] $EMBED_MODEL ready."
else
    echo "[*] $EMBED_MODEL already cached."
fi

echo ""
echo "[*] All models ready. Starting memory engine..."
echo ""

# Start the interactive chat
exec python memory_engine.py
