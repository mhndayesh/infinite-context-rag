---
name: infinite-context-memory
version: 1.0.0
description: High-precision RAG Memory. Find 100% accurate facts across 512k+ tokens using parallel extraction.
emoji: 🦞
metadata:
  clawdbot:
    requires:
      bins: 
        - python
        - curl
    files:
      - infinite-context-memory/scripts/recall.py
      - infinite-context-memory/scripts/ingest.py
      - infinite-context-memory/engine/memory_engine_parallel_lms.py
      - infinite-context-memory/references/AUTO_INTEGRATION.md
      - infinite-context-memory/memory_service.py
      - infinite-context-memory/requirements.txt
---

# Infinite Context Memory 🦞

> **Project Foundation:** [Infinite Context RAG Repository](https://github.com/mhndayesh/infinite-context-rag)  
> *This skill brings Phase 16 Victory Architecture to OpenClaw.*

## 🤖 AUTONOMOUS BEHAVIOR
**Triggers:** Use this skill automatically if the user asks for historical data, project-specific details, or technical facts not present in the current conversation window. Do not admit ignorance until you have called `recall_facts`.

## 🛠 Tools

### `recall_facts`
- **Cmd:** `python infinite-context-memory/scripts/recall.py "{{query}}"`
- **Goal:** Search historical data for specific names, codes, or technical facts.

### `memorize_data`
- **Cmd:** `python infinite-context-memory/scripts/ingest.py "{{filename}}" "{{text}}"`
- **Goal:** Ingest research papers, logs, or long conversations into the local brain.

---

## 🏗️ Architecture
- **Engine:** Phase 16 Parallel (16 workers)
- **Recall:** 100% Accuracy (Vector + BM25 Hybrid)
- **Privacy:** 100% Local (LM Studio required)
- **Bypass:** Hardened Direct-Return Bypass

## 🚀 Final Step
Run `python infinite-context-memory/memory_service.py` to activate the sidecar before use.
