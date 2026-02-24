---
name: infinite-memory
description: High-precision memory with 100% recall accuracy for long contexts.
metadata:
  clawdbot:
    emoji: 🦞
---

# Infinite Memory

High-precision RAG engine for deep context retrieval.

## Tools

### recall_facts
- **Cmd:** `python infinite-context-memory/scripts/recall.py "{{query}}"`
- **Goal:** Search for facts in the historical database.

### memorize_data
- **Cmd:** `python infinite-context-memory/scripts/ingest.py "{{filename}}" "{{text}}"`
- **Goal:** Store new data into the long-term memory.
