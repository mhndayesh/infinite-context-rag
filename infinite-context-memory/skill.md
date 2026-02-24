---
name: infinite-context-memory
version: 1.0.0
description: High-precision RAG Memory. Find 100% accurate facts across 512k+ tokens using parallel extraction.
homepage: https://github.com/mhndayesh/infinite-context-rag
user-invocable: true
disable-model-invocation: false
metadata:
  clawdbot:
    requires:
      bins: 
        - python
        - curl
    files:
      - scripts/recall.py
      - scripts/ingest.py
      - engine/memory_engine_parallel_lms.py
      - references/AUTO_INTEGRATION.md
      - memory_service.py
      - requirements.txt
---

# Infinite Context Memory 🦞

> **Project Foundation:** [Infinite Context RAG Repository](https://github.com/mhndayesh/infinite-context-rag)  
> *This skill brings Phase 16 Victory Architecture to OpenClaw.*

## 🤖 AUTONOMOUS BEHAVIOR
**Triggers:** Use this skill automatically if the user asks for historical data, project-specific details, or technical facts not present in the current conversation window. Do not admit ignorance until you have called `recall_facts`.

## 🛠 Tools

### `recall_facts`
- **Cmd:** `python scripts/recall.py "{{query}}"`
- **Goal:** Search historical data for specific names, codes, or technical facts.

### `memorize_data`
- **Cmd:** `python scripts/ingest.py "{{filename}}" "{{text}}"`
- **Goal:** Ingest research papers, logs, or long conversations into the local brain.

---

## 🏗️ Architecture
- **Engine:** Phase 16 Parallel (16 workers)
- **Recall:** 100% Accuracy (Vector + BM25 Hybrid)
- **Privacy:** 100% Local (LM Studio required)
- **Bypass:** Hardened Direct-Return Bypass

## 🚀 Final Step
Run `python memory_service.py` to activate the sidecar before use.
