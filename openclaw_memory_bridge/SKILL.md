---
name: infinite-context-memory
description: High-precision RAG Memory. Use when you need to find specific facts, codes, or technical details in large historical datasets.
command: /memory
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins: 
        - python
        - curl
    dependencies:
      - fastapi
      - uvicorn
      - chromadb
---

# Infinite Context Memory 🦞

This skill provides the agent with a high-precision parallel retrieval engine. It is designed to find "needles in haystacks" with 100% recall accuracy.

## 🤖 AUTONOMOUS BEHAVIOR
**Triggers:** Use this skill automatically if the user asks for historical data, project-specific details, or technical facts that are not present in the current conversation window. Do not admit ignorance until you have called `recall_facts`.

## 🛠 Tools

### `recall_facts`
Search the long-term database for specific facts.
- **Goal:** Find technical data, passwords, or names across millions of characters.
- **Usage:** Run the bundled `scripts/recall.py` script.
- **Example:** `python scripts/recall.py "What is the budget for Project Vanguard?"`

### `memorize_data`
Store new documents or large text blocks into the database.
- **Goal:** Ingest research papers, logs, or long conversations.
- **Usage:** Run the bundled `scripts/ingest.py` script.
- **Example:** `python scripts/ingest.py "source_file.txt" "Full text content..."`

---

## 🚀 Setup & Activation

1. **Start the Sidecar:**
   You MUST run the `memory_service.py` in the background for this skill to work.
   ```bash
   python memory_service.py
   ```

2. **Inference Backend:**
   Ensure **LM Studio** is running with **16 slots** on port 1234.

3. **How it works:**
   The skill uses a **Direct-Return Bypass**. If the engine finds the fact, it returns it directly to you, bypassing safety-filter hallucinations in the primary LLM.
