# Walkthrough: Phase VI (Single-Model Evaluation: Phi-4 Mini)

## Overview
We hypothesized that a unified architecture—using a single model for both generation and embeddings—might improve semantic mapping. We selected Microsoft's `phi4-mini:3.8b` for this experiment.

## What We Built
1. **Model Swap:** We temporarily removed `llama3.2:3b` and `nomic-embed-text`.
2. **Unified Endpoint:** We configured the engine to use `phi4-mini:3.8b` natively via Ollama for both chat inference and 384-dimensional vector embeddings.
3. **128k Stress Test:** We executed a scaled-down 128,000-token marathon to measure its performance.

## The Results
- **Feasibility:** The single-model architecture technically worked.
- **Performance Loss:** However, `phi4-mini:3.8b` struggled significantly with embedding latency compared to the highly optimized, purpose-built `nomic-embed-text`. Furthermore, the 4k context window proved too restricting for Phi-4's chattier baseline nature.
- **Conclusion:** We reverted the architecture back to the "Gold Standard" combination: `nomic-embed-text` for lightning-fast embeddings and `llama3.2:3b` for sharp, concise inference.
