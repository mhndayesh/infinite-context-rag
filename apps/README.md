# 🔌 Plug & Play — Agentic RAG Memory Engine

**Persistent, session-aware memory for any local LLM project.**  
Drop `memory_engine.py` into your project and call one function.

> Validated at **512,000 token depth** — 5/5 perfect recall using `phi4-mini:3.8b` on a single RTX 5070 12GB.

---

## ⚡ Quick Start

### Option A: Local (No Docker)

1. **Install dependencies:** `pip install chromadb ollama pynvml`
2. **Pull models:** `ollama pull phi4-mini:3.8b` and `ollama pull nomic-embed-text`
3. **Run:** `python memory_engine.py`

### Option B: Docker (Recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) with NVIDIA Container Toolkit (for GPU).

1. **Spin up the stack:**
   ```bash
   docker compose up -d
   ```
2. **Interactive chat:**
   ```bash
   docker compose run --rm memory-engine
   ```
   *(This auto-pulls all models and starts the chatbot)*

---

## ⚙️ Configuration

You can configure the engine via **environment variables** (in `docker-compose.yml` or your `.env`) or by editing **SECTION 2** of `memory_engine.py`:

```python
LLM_MODEL   = "phi4-mini:3.8b"      # swap to llama3.2:3b for lighter footprint
EMBED_MODEL = "nomic-embed-text"     # don't change this
DB_PATH     = "./memory_db"          # where your memory is stored on disk
OLLAMA_URL  = "http://localhost:11434"  # change if Ollama is on another machine
NUM_CTX     = 4096                   # 4096=safe, 8192=better quality
IDLE_TIMEOUT_SECONDS = 300           # new session block after 5min idle
```

All other code can be left untouched.

---

## 📋 Model Comparison

| Model | Score | Ingestion Time | VRAM |
|-------|:-----:|:--------------:|:----:|
| `phi4-mini:3.8b` ⭐ | **5/5** | 147s | ~6.4GB |
| `llama3.2:3b` | 4/5 | 134s | ~2.5GB |
| `llama3.1:8b` | untested | — | ~5GB |

> **Live VRAM log** (phi4-mini + nomic-embed-text running concurrently):  
> `total: 12.8GB · free: 6.45GB · used: ~6.37GB`

---

## 🧩 Integration Examples

See [`example_chat.py`](example_chat.py) for ready-to-run code:

| Example | Use case |
|---------|----------|
| `example_1_simple()` | Store a fact, recall it later |
| `example_2_interactive_loop()` | Standalone chatbot |
| `example_3_agent_wrapper()` | Drop into any AI agent |
| `example_4_api_handler()` | FastAPI / Flask REST endpoint |
| `example_5_batch_ingest()` | Pre-load documents before a chat |

Run interactively:
```bash
python example_chat.py
```

---

## 🔁 How It Works (brief)

```
Your message
  ↓  1. LLM rewrites your query into dense search keywords
  ↓  2. ChromaDB finds top 10 closest chunks (vector search)
  ↓  3. LLM picks the best match (agentic routing)
  ↓  4. Entire conversation block reassembled around the match
  ↓  5. Key entities (names, numbers, dates) prepended as cheat sheet
  ↓  6. Long context split into pages, each read independently
  ↓  7. Final answer generated (4,096 token context window)
  ↓  8. Conversation saved to ChromaDB in background thread
```

**Key insight:** The LLM never sees more than 4,096 tokens at once. The RAG pipeline surfaces only the right ~1,500 characters from a database up to 512,000 tokens deep.

---

## 📁 Files

| File | Description |
|------|-------------|
| `memory_engine.py` | The engine — copy this into your project |
| `example_chat.py` | Integration examples for 5 common use cases |
| `README.md` | This file |

---

## 🐛 Troubleshooting

**"connection refused" error**  
→ Make sure Ollama is running: `ollama serve`

**Model not found**  
→ Pull it first: `ollama pull phi4-mini:3.8b`

**Out of VRAM**  
→ Lower `NUM_CTX` to 2048, or switch to `llama3.2:3b` (lighter)

**Wrong answers**  
→ Try being more specific: `"Please remember: budget is exactly $120,000"` instead of `"the budget is 120k"`

**Memory grows too large**  
→ Delete the `./memory_db/` folder to start fresh. Or change `DB_PATH` to a new folder.

---

## 📄 From the research

This engine was the best performer across 6 experiments at 512k token depth.  
Full benchmark results and technical paper: [github.com/mhndayesh/infinite-context-rag](https://github.com/mhndayesh/infinite-context-rag)
