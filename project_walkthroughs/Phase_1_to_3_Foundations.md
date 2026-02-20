# Walkthrough: Phases I - III (Foundations & Baseline Tests)

## Overview
The goal of the early phases was to establish a functional, hardware-safe baseline for persistent memory. LLMs traditionally suffer from strict context window limits. We needed a system that could store user chat history indefinitely without crashing the local GPU.

## What We Built
1. **Core Memory Engine:** We developed `memory_engine.py` using `nomic-embed-text` for vector embeddings and ChromaDB for local, disk-based storage.
2. **Context Window Guard:** We implemented a strict 4,000 token limit (`num_ctx: 4096`) for the `llama3.2:3b` inference model to ensure stability on consumer hardware.
3. **Dynamic Prompt Chunking:** To protect against massive user pastes, we added logic to split large inputs (>2000 chars) into manageable chunks, embedding them instantly in the background.

## The Results (Torture Test)
We ran a foundational "Torture Test" to evaluate how well the standard vector pipeline recalled facts injected over long conversations.
- **Outcome:** The system successfully ran, but pure snippet-based retrieval (Standard RAG) proved insufficient. It extracted disjointed sentences that lacked surrounding conversational context, prompting the need for further architectural evolution.
