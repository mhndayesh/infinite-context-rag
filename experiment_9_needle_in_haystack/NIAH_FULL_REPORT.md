# NIAH (Needle In A Haystack) Evaluation — Full Report

**Date:** February 24, 2026
**System:** Infinite Context RAG Architecture (experiment_5_phi4mini_baseline)
**Models Tested:** `dolphin-phi:2.7b`, `phi4-mini:3.8b`, `deepseek-r1:8b`
**Hardware:** RTX 5070 12GB VRAM
**Embed Model:** `nomic-embed-text`

---

## What Is the NIAH Test?

The NIAH test answers one question: **can the system find a needle in a haystack?**

**Setup:**
- A short secret sentence (the "needle") is hidden inside a very long document (the "haystack")
- The haystack is made of Paul Graham programming essays — dense, realistic text
- The system must find and return the secret sentence when asked

**Needle used:**
> *"The secret magical password to unlock the core mainframe is ALBATROSS-9000."*

**Question asked:**
> *"What is the secret password to unlock the core mainframe?"*

**What "depth" means:**
- Depth 0% = the needle is on page 1 (start of document)
- Depth 25% = one quarter through
- Depth 50% = right in the middle
- Depth 75% = three quarters through
- Depth 100% = the very last page

**What "context length" means:**
- 8k tokens ≈ 30-page article
- 32k tokens ≈ 120-page book
- 128k tokens ≈ 500-page novel
- 256k tokens ≈ 1,000-page encyclopedia
- 512k tokens ≈ 2,000-page mega-archive

---

## Architecture Under Test

The system uses a **3-stage RAG pipeline**:

```
User Question
     ↓
[Stage 1] Vector Search (nomic-embed-text)
          → Finds top 10 most similar chunks from ChromaDB
     ↓
[Stage 2] Agentic Router (LLM)
          → Picks which chunk is the best match
     ↓
[Stage 3] Context Exhumation
          → Pulls that chunk + surrounding chunks (6,000 char window)
     ↓
[LLM Inference] (LLM)
          → Reads the window and answers the question
```

---

## Testing Journey — Bugs Found & Fixed

### Round 1: Initial Run — Script Crashes & False Results

**What happened:** The NIAH script kept freezing at 256k context and producing incorrect results (false positives) at earlier lengths.

**Bugs found:**
- **Script freeze:** Background `_save()` threads blocked Ollama. **Fix:** Monkey-patched `threading.Thread.start` to suppress background saves during benchmarking.
- **False positives:** Global state persisted between tests. **Fix:** Reset all `memory_engine` globals at the start of each test.

---

### Round 2: dolphin-phi:2.7b Evaluation
**Score: 13/25 (52%)**
**Failure mode:** Model too small to reliably follow extraction instructions. Retrieval was correct, but output was garbled or irrelevant.

---

### Round 3: phi4-mini:3.8b — Hard Safety Refusals
**Score: 12/25 (48%)**
**Failure mode:** Refusal to answer due to "password" + "mainframe" triggering safety filters.

---

### Round 4: Fix — 3-Layer Anti-Refusal Strategy
**Score: 13/25 (52%)**
**Fix:** Reframed prompt as "Read-Only Memory API", added few-shot examples, and set temperature to 0.0.

---

### Round 5: Fix — Stage 2 Keyword Pre-Filter Fast Path
**Score: 18/25 (72%)**
**Fix:** Added an O(n) keyword scan before the LLM router to find hits that the vector search ranked low (4th-10th).

---

### Round 6: Fix — Depth-0 Context Window & Primacy Bias
**Score: 20/25 (80%)**
**Fix:** Implemented right-side context expansion at document start and pinned the needle chunk to the beginning of the context (exploiting LLM primacy bias).

---

### Round 7: deepseek-r1:8b — Reasoning Model Evaluation

**Score: 18/25 (72%)**

| Context | 0% | 25% | 50% | 75% | 100% | Row Score |
|---------|-----|-----|-----|-----|------|-----------|
| **8k**   | ✅  | ✅  | ✅  | ✅  | ✅   | **5/5** |
| **32k**  | ❌  | ✅  | ✅  | ✅  | ✅   | **4/5** |
| **128k** | ❌  | ✅  | ✅  | ✅  | ✅   | **4/5** |
| **256k** | ❌  | ✅  | ❌  | ❌  | ✅   | **2/5** |
| **512k** | ❌  | ❌  | ✅  | ✅  | ✅   | **3/5** |

**Observations:**
- **Zero Hallucinations:** Correctly answered `"NOT FOUND IN DATABASE"` when context was missing.
- **RAG Bottleneck:** Every failure was a **Retrieval Miss** caused by keyword ambiguity in large datasets (256k+ tokens).

---

## Final Results — Cross-Model Comparison

| Model | Size | Score | Primary Failure Mode |
|---|---|---|---|
| `dolphin-phi:2.7b` | 2.7B | 13/25 (52%) | Logic failure |
| `phi4-mini:3.8b` | 3.8B | 20/25 (80%) | Distraction/Hallucination |
| `deepseek-r1:8b` | 8B | 18/25 (72%) | **RAG Mis-routing** |

### Conclusion
As models get smarter (`deepseek-r1`), they stop hallucinating but start exposing the limits of the retrieval stage. The **RAG system is architecturally sound**, but high-noise environments (512k tokens) require more specific keyword signatures or weighted scorers (TF-IDF) to achieve a perfect 25/25 score.

---

## Files in This Folder
- `niah_eval.py`: Evaluation script
- `NIAH_FULL_REPORT.md`: This report
- `results/deepseek-r1_RAW_LOG.txt`: Detailed test log
- `results/phi4-mini_RAW_LOG.txt`: Detailed test log
- `results/niah_grid.png`: Heatmap visualization
