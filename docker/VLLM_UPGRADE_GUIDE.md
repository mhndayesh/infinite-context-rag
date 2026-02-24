# Phase XV: vLLM Upgrade Guide

## Overview
This folder contains the configuration to switch from **Ollama → vLLM** for the async parallel extraction phase, unlocking **true 3-4x GPU speedup**.

## Why vLLM Changes Everything

With Ollama: `asyncio.gather(chunk1, chunk2, chunk3, chunk4)` → still Serial (queue)
With vLLM:   `asyncio.gather(chunk1, chunk2, chunk3, chunk4)` → Real Parallel (GPU batching)

vLLM uses PagedAttention and Continuous Batching — the GPU processes ALL requests simultaneously.

## Upgrade Steps

### 1. Install vLLM (Linux/WSL2 recommended)
```bash
pip install vllm
```

### 2. Start the vLLM server with your model
```bash
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1-Distill-Llama-8B \
    --host 0.0.0.0 --port 8000
```

### 3. Enable Phase XV in memory_engine.py
```python
# Change these 2 lines:
ASYNC_EXTRACTION_ENABLED = True          # was False
OLLAMA_HTTP_URL = "http://localhost:8000/v1/chat/completions"  # was Ollama URL
```

### 4. Update the payload format (OpenAI-compatible)
The `async_extract_chunk` function's payload already uses the OpenAI messages format.
vLLM's `/v1/chat/completions` endpoint accepts it directly — no other changes needed.

## Expected Results

| Metric       | Ollama    | vLLM      |
|-------------|-----------|-----------|
| 4 Chunk Extraction | ~20s (serial) | ~5s (parallel) |
| Answer Accuracy | 100% | 100% |
| GPU Utilization | ~40% | ~90% |

## Docker Integration
See `docker/docker-compose.vllm.yml` for a ready-to-use full-stack configuration.
