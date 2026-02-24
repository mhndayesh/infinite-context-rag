# Experiment 10: Phase XV — Async Parallel Extraction (Map-Reduce)

> **Status:** ✅ Architecture Implemented & Verified | ⏳ vLLM Upgrade Pending
>
> **Accuracy:** 100% (PASS on 32k Paul Graham news haystack with ALBATROSS-9000 needle at 25% depth)

---

## The Problem: Sequential Extraction is the Bottleneck

After achieving **100% recall** in Experiment 9, the pipeline still had one remaining bottleneck: **sequential paged context reading**. When the retrieved context window is large (6,000+ chars), the LLM must read it in serial passes. Each pass costs 3-5s on `deepseek-r1:8b`.

**Before Phase XV:** `read(page1) → wait → read(page2) → wait → read(page3)`
**After Phase XV:** `asyncio.gather(read(page1), read(page2), read(page3))` (all fire simultaneously)

---

## Architecture: Additive Map-Reduce

```
Retrieved Context (6,000 chars)
         │
         ▼
    SPLIT into N pages (1,500 chars each)
         │
    ┌────┴────────────────────────────────┐
    │  MAP: asyncio.gather fires N workers  │
    │  Each worker: async HTTP → LLM        │
    │  Extract only the relevant fact       │
    └────┬────────────────────────────────┘
         │
    REDUCE: Merge non-None findings
         │
         ▼
  ┌────────────────────────────────┐
  │ CHEAT SHEET (prepended)        │   ← Phase XV output
  │ FULL RAW CONTEXT (preserved)   │   ← Original context (safety net)
  └────────────────────────────────┘
         │
         ▼
  Final LLM Inference (4k window)
```

**Key Design Principle:** The cheat sheet is **PREPENDED**, never replacing the raw context. If an extraction worker misses the needle, the LLM still sees it in the full context. This preserves 100% accuracy.

---

## Benchmark Results (Summary)

| Scenario | ASYNC ON | ASYNC OFF | Engine |
|----------|----------|-----------|--------|
| Memory DB (Session Logs) | **7.4s** ✅ | 20.7s | Ollama |
| News Haystack (32k tokens) | 22.9s ✅ | **16.3s** | Ollama |

**Finding:** Ollama queues requests serially, so async.gather doesn't provide true GPU parallelism on extraction. However, the full pipeline still benefits in session-log scenarios.

See [`results/BENCHMARK_RESULTS.md`](results/BENCHMARK_RESULTS.md) for full details.

---

## Files

| File | Description |
|------|-------------|
| `src/memory_engine.py` | Full engine with Phase XV implemented |
| `benchmarks/phase15_benchmark.py` | Speed comparison: ASYNC ON vs OFF |
| `benchmarks/phase15_news_benchmark.py` | 32k news haystack benchmark |
| `results/BENCHMARK_RESULTS.md` | Detailed benchmark findings |
| `VLLM_UPGRADE_GUIDE.md` | 3-step guide to enable true GPU parallelism |

---

## Quick Start

```bash
# Install Phase XV dependency
pip install aiohttp

# Run the memory DB benchmark (compare async ON vs OFF)
cd benchmarks
python phase15_benchmark.py

# Run the 32k news haystack benchmark
cd ..
python benchmarks/phase15_news_benchmark.py
```

---

## Phase XVI: vLLM Upgrade (Next)

Swapping Ollama → vLLM enables **Continuous Batching (PagedAttention)**. With vLLM:
- `asyncio.gather(4 chunks)` → **genuine 4-way GPU parallelism**
- Expected: **~5s extraction** (vs 20s with Ollama)
- Requires: `ASYNC_EXTRACTION_ENABLED = True` + `OLLAMA_HTTP_URL = "http://localhost:8000/v1/chat/completions"`

See [`VLLM_UPGRADE_GUIDE.md`](VLLM_UPGRADE_GUIDE.md) for full instructions.

---

## Configuration (in `src/memory_engine.py`)

```python
# Phase XV toggles
ASYNC_EXTRACTION_ENABLED = False  # Set to True with vLLM
EXTRACTION_PAGE_SIZE = 1500       # ~375 tokens per chunk
OLLAMA_HTTP_URL = "http://localhost:11434/api/chat"
# For vLLM: "http://localhost:8000/v1/chat/completions"
```
