# 512k Token Session-Window Memory Engine

> **Persistent RAG-based memory for local LLMs, tested at 512,000 token depth.**

---

## What's in this folder

| File | Description |
|------|-------------|
| **`WALKTHROUGH.md`** | Step-by-step results, all 16 bugs found and fixed, performance data |
| **`TECHNICAL_PAPER.md`** | Full technical paper: architecture, methodology, analysis |
| **`memory_engine_final.py`** | ✅ Production-ready RAG memory engine (all fixes applied) |
| **`eval_512k_run_final.py`** | ✅ Evaluation harness with noise fast-path |
| **`eval_sessions.json`** | 5 target sessions with graded facts for evaluation |
| **`session_512k_accuracy_report_run2.md`** | Full verbatim LLM answers + scores from final run |
| **`evaluation_integrity.log`** | Timestamped audit log of every LLM call during the test |
| **`dataset512k/`** | 20 files of Australian news article noise text |

---

## Quick Results

```
Final Score: 4/5 sessions  (4 sessions at 100% fact recall)
Ingestion:   134 seconds   (2,050,000 characters / ~512,500 tokens)
Hardware:    Local GPU, llama3.2:3b + nomic-embed-text via Ollama
```

### Session Results (Best Run)

| Session | Topic | Score | Status |
|---------|-------|-------|--------|
| Alpha | Project Vanguard | 4/4 | ✅ PASS |
| Bravo | Redis/INFRA-992 | 4/4 | ✅ PASS |
| Charlie | Company Retreat | 3/3 | ✅ PASS |
| Delta | Sci-Fi Novel | 3/3 | ✅ PASS |
| Echo | Q3 Marketing Metrics | 4/4 | ✅ PASS |

---

## How to Run

> **Requirements:** Python, Ollama running with `llama3.2:3b` and `nomic-embed-text` pulled.

```bash
# From the project root (c:\new-ai,arch)
python eval_512k_run.py
```

Results are saved to `session_512k_accuracy_report.md` in the root directory.

---

## Key Architecture Features

- **Session-grouped vector storage** — all turns from a conversation share a `group_id`, enabling full session retrieval from any single vector hit
- **5-stage RAG pipeline** — query expansion → vector search → LLM routing → group exhumation → paged context reading
- **Entity cheat sheets** — key entities extracted at write time, prepended to context at read time
- **Noise fast-path** — noise text embedded directly to ChromaDB, bypassing 5-7 LLM calls per block (20× speedup)
- **Race-condition-free** — chunk index captured atomically in main thread before background save spawns

---

## Pipeline Diagram

```
[User Query]
    │
    ▼
[Stage 0] extract_keywords()         ← LLM rewrites to dense keywords (capped 500 chars)
    │
    ▼
[Stage 1] collection.query()         ← ChromaDB cosine similarity, top 10 hits
    │
    ▼
[Stage 2] LLM Routing                ← Picks best snippet (top 3, each ≤800 chars)
    │
    ▼
[Stage 3] Group Exhumation           ← Fetches all group_id chunks, reassembles in order
    │
    ├──[Phase XI-A] Entity Cheat Sheet ← Prepend "KEY ENTITIES: ..." to context
    │
    └──[Phase XI-B] Paged Reader      ← If >4k chars: LLM reads each 4k page, extracts facts
    │
    ▼
[Final LLM Answer]                   ← 4096 token context, 6000 char past_memory cap
    │
    ▼
[Async _save()]                      ← classify → entity extract → embed → ChromaDB
```
