# Walkthrough: Phase V (Performance Profiling)

## Overview
Before attempting to fix the recall accuracy issues discovered in Phase IV, we needed to ensure the latency of our architecture was viable for a real-time chat agent.

## What We Built
We instrumented `memory_engine.py` with high-resolution timing hooks (`time.perf_counter()`). We specifically tracked:
1. **Retrieval Latency:** Time spent querying ChromaDB.
2. **Inference Latency:** Time spent by `llama3.2:3b` generating the final response.
3. **Save/Embed Latency:** Time spent generating embeddings with `nomic-embed-text` and writing to disk.

## The Results
- **Vector Search (ChromaDB):** Outstanding. Even with 512k tokens in the database, query times remained well under 50ms.
- **Inference (Llama 3.2 3B):** Highly performant. Time-to-first-token and total generation rarely exceeded 1 second for factual retrieval.
- **Embedding Bottleneck:** The primary bottleneck was the embedding process. To resolve this, we shifted ingestion out of the main thread and into background daemon threads, ensuring the UI remained perfectly responsive even when processing large pastes.
