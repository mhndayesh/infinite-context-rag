# Agentic RAG Memory Architecture

This repository contains the culmination of a 9-phase architectural journey to build a boundless, hardware-safe, and highly contextual persistent memory system for Large Language Models.

We solved the industry-standard "Semantic Dilution" problem (where Vector Databases fail to find relevant conversational history amidst massive noise floors) by implementing a novel blend of **Chronological Session-Window Extraction** and **Agentic Query Expansion**.

## The Architecture
The conventional approach to LLM memory relies on "Semantic Chunking" and naive RAG, which breaks documents into disjointed sentences and loses conversational flow.

Our architecture features a refined two-stage retrieval pipeline:

### 1. Agentic Pre-Search Expansion (Phase IX)
Instead of searching ChromaDB using casual human language (which fails against 128k+ characters of noise), an incredibly fast LLM intercepts the query. It translates conversational intent into a dense, comma-separated payload of exact keywords. This acts as a laser-guided search, instantly surfacing the concealed target vectors with a 100% success rate (5/5 retrieval score on 32k-token evaluations).

### 2. Session-Window Block Retrieval (Phase VIII)
When the Vector DB hits a mathematical match, it doesn't return the isolated sentence. Utilizing a custom `session_block_id` managed by a time-based IDLE_TIMEOUT, the system exhumes the *entire sequential conversational block* that the sentence resided in. 

The LLM is handed a perfectly clean, contextual, and chronological timeline to read from.

## Hardware Safe
The entire system functions flawlessly while remaining strictly locked within a **4,000 token Context Window**, preventing out-of-memory crashes on consumer GPUs.

## Project Documentation
You can explore the full history of the project, including performance profiling, failed experiments, and the final architectural victory, in the `project_walkthroughs` folder:
- [Phase 1-3: Foundations](project_walkthroughs/Phase_1_to_3_Foundations.md)
- [Phase 4: The News Marathon (Semantic Dilution)](project_walkthroughs/Phase_4_News_Marathon.md)
- [Phase 5: Performance Profiling](project_walkthroughs/Phase_5_Performance_Profiling.md)
- [Phase 6: Single-Model Attempts](project_walkthroughs/Phase_6_Phi4_Mini.md)
- [Phase 7: Two-Stage RAG](project_walkthroughs/Phase_7_Two_Stage_RAG.md)
- [Phase 8: Session-Window Blocks](project_walkthroughs/Phase_8_Session_Window_Blocks.md)
- [Phase 9: Victory (Keyword Expansion)](project_walkthroughs/Phase_9_SUCCESS_Keyword_Expansion.md)

## Requirements
- Python 3.10+
- `chromadb`
- `ollama`
- Models: `llama3.2:3b` (Inference/Expansion), `nomic-embed-text` (Embeddings)

## Usage
Simply start the engine and chat naturally. The Agentic framework handles the memory processing entirely in the background.

```bash
python memory_engine.py
```
