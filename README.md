# Agentic RAG Memory Architecture

> **Persistent, session-aware memory for local LLMs — validated at 100% (25/25) accuracy on 512,000 token depth.**  
> No fine-tuning. No cloud API. Zero cost per query. Complete data privacy.

---

## 🚀 NEW: Phase 16 Breakthrough (Feb 24, 2026)
The architecture has been upgraded to a **High-Precision Parallel Engine**. 

**Latest Stats:**
- **Accuracy:** 100% (25/25) across all depths.
- **Speed:** ~7.5s total pipeline (3x speedup via 16 parallel extraction slots).
- **Hardened:** Zero safety refusals via the novel **Direct-Return Bypass**.

### 📂 Repository Structure

| Folder | Description |
| :--- | :--- |
| [**🚀 apps/**](apps/) | **Start Here.** User-friendly chat interface and data ingestor. |
| [**🏆 core/**](core/) | The production-ready 100% accuracy RAG engine. |
| [**📖 docs/**](docs/) | Technical papers and the 16-phase architectural journey. |
| [**📦 archive/**](archive/) | All 15+ experimental phases, research logs, and legacy code. |

---

## 🛠 Quick Start

1. **Start LM Studio Server** (Set slots to 16, context to 8192).
2. **Ingest Data:** Drop `.txt` files in `apps/source_docs/` and run `python apps/INGEST_DATA.py`.
3. **Chat:** Run `python apps/QUICK_START_CHAT.py`.

---

## 🏆 THE ULTIMATE VICTORY: 100% Recall at 512k Context

The system has overcome the "Semantic Noise" ceiling by implementing **Hybrid Stage 1 Retrieval (RRF)**. It now retrieves "hidden needles" with perfect precision even when they are buried at the very beginning of a 2,000,000-character document.

- **Stage 1 Recall:** 100% (Vector + BM25 Hybrid)
- **Stage 2 Routing:** 100% (BM25 Reranker)
- **Total Pipeline:** ~6-8s (Local `deepseek-r1:8b`)

---

## 📖 Key Documentation
- [**FULL ARCHITECTURAL JOURNEY**](docs/FULL_ARCHITECTURAL_JOURNEY_INFINITE_CONTEXT_RAG.md) - The 16-phase chronicle from failure to 100% success.
- [**TECHNICAL DEEP DIVE**](docs/TECHNICAL_DEEP_DIVE.md) - Deep math/logic behind RRF, Parallel Mapping, and Bypass.
- [**VALUE PROPOSITION**](archive/perfect%20recal%20512k/VALUE_PROPOSITION.md) - Why local infinite-context RAG is the future.

---

## 📊 Historical Milestone: `phi4-mini:3.8b` + Baseline RAG — **5/5 Score**
*(Previous breakthrough on 32k-128k context ranges)*

> 📁 Code: [`archive/experiment_5_phi4mini_baseline/`](archive/experiment_5_phi4mini_baseline/)  
> 📄 Results: [`archive/research_papers_and_reports/session_512k_accuracy_report.md`](archive/research_papers_and_reports/session_512k_accuracy_report.md)

---

## 📊 Full Benchmark — All 4 Methods × Both Models

| Method | `llama3.2:3b` Score | `llama3.2:3b` Time | `phi4-mini:3.8b` Score | `phi4-mini:3.8b` Time |
|--------|:-------------------:|:------------------:|:----------------------:|:---------------------:|
| **Baseline RAG** ⭐ | 4/5 | 134s | **5/5** ✅ | **147s** |
| **Forced CoT** `<think>` | 1/5 | 190s | **5/5** ✅ | 235s |
| **Agentic Ctrl-F** | 2/5 | 187s | 3/5 | 280s |

> Hardware: Intel i7-14700F · 64GB RAM · NVIDIA RTX 5070 12GB VRAM · Ollama local inference  

---

## Requirements
- Python 3.10+
- `chromadb`
- `ollama` (for embeddings)
- `lm-studio` (for high-speed parallel inference)
- `pynvml` (optional — VRAM monitoring)
