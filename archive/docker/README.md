# 🐳 Infinite Context RAG — Docker Setup

This directory contains the optimized Docker configuration for the **100% Recall** RAG engine.

## 🚀 Quick Start (Complete Stack)

To start the full stack (Ollama + RAG Engine) with GPU acceleration:

```bash
docker compose up -d
```

### 💬 Start an Interactive Chat
Once the containers are up and the models are pulled (check `docker logs ollama`), run:

```bash
docker compose run --rm rag-engine
```

### 📊 Run the 512k NIAH Benchmark
To run the full Needle-In-A-Haystack benchmark inside the container:

```bash
docker compose run --rm rag-engine niah_eval.py
```

## ⚙️ Configuration
You can modify the following variables in `docker-compose.yml`:
- `LLM_MODEL`: Reasoning model (e.g., `deepseek-r1:8b`).
- `EMBED_MODEL`: Embedding model (e.g., `nomic-embed-text`).
- `NUM_CTX`: Token context window (e.g., `4096`).

## 💾 Persistence
- **Models:** Stored in the `ollama_models` volume.
- **Memory:** Stored in the `memory_db` volume.
To wipe everything and start fresh: `docker compose down -v`.

---
*Optimized for NVIDIA GPUs via NVIDIA Container Toolkit.*
