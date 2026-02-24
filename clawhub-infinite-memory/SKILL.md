---
name: infinite-memory
version: 1.0.0
description: High-precision RAG Memory. Find 100% accurate facts across 512k+ tokens using parallel extraction.
emoji: 🦞
metadata:
  clawdbot:
    requires:
      bins: 
        - python
    files:
      - scripts/recall.py
      - scripts/ingest.py
      - engine/memory_engine_parallel_lms.py
      - references/AUTO_INTEGRATION.md
      - memory_service.py
      - requirements.txt
      - INSTALL.md
---

# Infinite Memory 🦞

High-precision RAG engine for deep context retrieval (Phase 16 Architecture).

## ⚙️ Setup Instructions
To use this memory, follow these steps:
1.  **Install Dependencies:** Run `pip install -r requirements.txt`.
2.  **Start Sidecar:** Run `python memory_service.py`. The service binds to `127.0.0.1` for maximum security.
3.  **LM Studio:** Ensure LM Studio is running on `localhost:1234`.

## 🗄️ Database Location
- The underlying high-precision database is stored in: `infinite-context-memory/memory_db/`
- This folder is created automatically upon the first ingestion.

## 🤖 Agent Instructions
You are equipped with a high-precision Infinite Context Memory. 
- **Strategic Retrieval:** Use `recall_facts` automatically if the user asks about facts not in your current window to provide accurate historical context.
- **Assisted Memorization:** Propose using `memorize_data` to store important chat summaries or technical documentation. Always confirm with the user before storing sensitive or personal data.
- **Grounding:** Use the output of `recall_facts` as a highly reliable reference for project history and past decisions.

## 🛠 Tools

### `recall_facts`
- **Cmd:** `python scripts/recall.py "{{query}}"`
- **Goal:** Search historical data for specific names, codes, or technical facts.

### `memorize_data`
- **Cmd:** `python scripts/ingest.py "{{filename}}" "{{text}}"`
- **Goal:** Ingest research papers, logs, or long conversations into the local brain.
