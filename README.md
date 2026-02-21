# Agentic RAG Memory Architecture

This repository contains the culmination of a multi-phase architectural journey to build a boundless, hardware-safe, and highly contextual persistent memory system for Large Language Models.

We solved the industry-standard **"Semantic Dilution"** problem (where Vector Databases fail to find relevant conversational history amidst massive noise floors) by implementing a novel blend of **Chronological Session-Window Extraction**, **Agentic Query Expansion**, and **Entity Cheat Sheet Retrieval** — validated at **512,000 token depth** on consumer GPU hardware.

---

## The Architecture

The conventional approach to LLM memory relies on "Semantic Chunking" and naive RAG, which breaks documents into disjointed sentences and loses conversational flow.

Our architecture features a refined multi-stage retrieval pipeline:

### 1. Agentic Pre-Search Expansion (Phase IX)
Instead of searching ChromaDB using casual human language (which fails against 128k+ characters of noise), an incredibly fast LLM intercepts the query. It translates conversational intent into a dense, comma-separated payload of exact keywords — deduplicated and capped at 500 chars to prevent embedding overflow. This acts as a laser-guided search, instantly surfacing the concealed target vectors.

### 2. Session-Window Block Retrieval (Phase VIII)
When the Vector DB hits a mathematical match, it doesn't return the isolated sentence. Utilizing a custom `session_block_id` managed by a time-based `IDLE_TIMEOUT`, the system exhumes the *entire sequential conversational block* that the sentence resided in. The LLM is handed a perfectly clean, contextual, and chronological timeline to read from.

### 3. Entity Cheat Sheets (Phase XI-A)
At write time, key entities (names, numbers, dates, technical IDs) are extracted from each stored turn and saved in ChromaDB metadata. At read time, these are prepended to the top of the context window as `KEY ENTITIES: Dr. Elena Rostova, 850 million euros, Leviathan...` — ensuring critical facts survive the context window budget even if the raw text is condensed.

### 4. Paged Context Reading (Phase XI-B)
When the exhumed session block exceeds 4,000 characters, it is split into pages. The LLM reads each page independently, extracting only the facts relevant to the user's question. This prevents "Lost in the Middle" fatigue and reduces context size from ~6,000 chars to ~1,500 chars of pure targeted facts.

---

## Hardware Safe
The entire system functions while remaining strictly locked within a **4,096 token Context Window**, preventing out-of-memory crashes on consumer GPUs. All embedding inputs are hard-capped at 2,000 characters to stay within `nomic-embed-text`'s safe operating range.

---

## 512k Token Stress Test Results (Phase X)

The system was validated by burying 5 target conversational sessions inside **820 blocks of 2,500-character news article noise** — totalling **~512,500 tokens (2,050,000 characters)** of memory depth on `llama3.2:3b`.

| Session | Topic | Score | Status |
|---------|-------|-------|--------|
| Alpha | Project Vanguard (submersible) | 4/4 | ✅ PASS |
| Bravo | Redis/INFRA-992 debugging | 4/4 | ✅ PASS |
| Charlie | Company retreat | 3/3 | ✅ PASS |
| Delta | Sci-fi novel characters | 3/3 | ✅ PASS |
| Echo | Q3 marketing metrics | 4/4 | ✅ PASS |

**Final Score: 4/5 sessions recalled perfectly on a single run.**  
**Ingestion time: 134 seconds** (down from 65+ minutes — 20× speedup via noise fast-path).

> 📁 See [`512k_window_evaluation/`](512k_window_evaluation/) for full documentation.

---

## Bug Fixes (16 Total — Phase XI Audit)

A comprehensive 3-pass audit of `memory_engine.py` found and fixed 16 bugs ranging from embedding overflow crashes to chunk index race conditions:

| Category | Bugs Fixed |
|----------|-----------|
| Embedding overflow (Ollama crashes) | 3 |
| LLM context window overflow (3-min freezes) | 2 |
| Race conditions on shared state | 2 |
| Duplicate DB entries per noise block | 1 |
| Dead code / duplicate imports | 3 |
| Grading logic (false failures) | 1 |
| Data quality (truncation, dedup) | 4 |

> 📄 Full bug table: [`512k_window_evaluation/WALKTHROUGH.md`](512k_window_evaluation/WALKTHROUGH.md)  
> 📄 Technical deep-dive: [`512k_window_evaluation/TECHNICAL_PAPER.md`](512k_window_evaluation/TECHNICAL_PAPER.md)

---

## Project Documentation

Full history including performance profiling, failed experiments, and architectural evolution:

- [Phase 1-3: Foundations](project_walkthroughs/Phase_1_to_3_Foundations.md)
- [Phase 4: The News Marathon (Semantic Dilution)](project_walkthroughs/Phase_4_News_Marathon.md)
- [Phase 5: Performance Profiling](project_walkthroughs/Phase_5_Performance_Profiling.md)
- [Phase 6: Single-Model Attempts](project_walkthroughs/Phase_6_Phi4_Mini.md)
- [Phase 7: Two-Stage RAG](project_walkthroughs/Phase_7_Two_Stage_RAG.md)
- [Phase 8: Session-Window Blocks](project_walkthroughs/Phase_8_Session_Window_Blocks.md)
- [Phase 9: Victory (Keyword Expansion)](project_walkthroughs/Phase_9_SUCCESS_Keyword_Expansion.md)
- [Phase 10-11: 512k Stress Test + Audit](512k_window_evaluation/WALKTHROUGH.md)

---

## 512k Evaluation Files

| File | Description |
|------|-------------|
| [`512k_window_evaluation/memory_engine_final.py`](512k_window_evaluation/memory_engine_final.py) | Production RAG engine — all 16 fixes applied |
| [`512k_window_evaluation/eval_512k_run_final.py`](512k_window_evaluation/eval_512k_run_final.py) | Evaluation harness with noise fast-path |
| [`512k_window_evaluation/eval_sessions.json`](512k_window_evaluation/eval_sessions.json) | 5 target sessions with graded facts |
| [`512k_window_evaluation/session_512k_accuracy_report_run2.md`](512k_window_evaluation/session_512k_accuracy_report_run2.md) | Full verbatim LLM answers + scores |
| [`512k_window_evaluation/TECHNICAL_PAPER.md`](512k_window_evaluation/TECHNICAL_PAPER.md) | Full architecture paper |
| [`512k_window_evaluation/WALKTHROUGH.md`](512k_window_evaluation/WALKTHROUGH.md) | Bug table, results, run comparison |

---

## Requirements
- Python 3.10+
- `chromadb`
- `ollama`
- `pynvml` (optional — VRAM monitoring)
- Models: `llama3.2:3b` (inference/expansion/classification), `nomic-embed-text` (embeddings)

## Usage

```bash
# Run the memory engine interactively
python memory_engine.py

# Run the 512k stress test evaluation
python eval_512k_run.py
```
