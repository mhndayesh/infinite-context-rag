# Walkthrough: Phase VII (Two-Stage Agentic RAG)

## Overview
Returning to the primary challenge (Semantic Dilution and fragmented recall), we redesigned the RAG (Retrieval-Augmented Generation) pipeline. Standard RAG grabs disjointed sentences based on mathematical similarity. We needed *context*.

## What We Built
We implemented a **Two-Stage Agentic Router**:
1. **Stage 1 (Broad Net):** ChromaDB returns the Top 10 most mathematically relevant snippets.
2. **Stage 2 (Agentic Selection):** Instead of blindly passing those snippets to the user, we feed them into a hidden "Router" LLM prompt. The LLM acts as an arbiter, reading the snippets and outputting the specific index (0-9) of the *most* logically correct hit for the user's question.
3. **Stage 3 (Full Exhumation):** Once the exact center-point is identified, the system leverages `group_id` metadata to pull the surrounding database chunks, rebuilding the full, unabridged document context around the hit.

## The Results
This was a massive leap forward. Instead of an AI answering a question using a fragmented, out-of-context sentence, it now had access to the full paragraph surrounding the fact. However, it still struggled to logically group natural conversational turns.
