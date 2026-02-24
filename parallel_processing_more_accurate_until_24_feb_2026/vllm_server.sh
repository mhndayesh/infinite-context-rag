#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Phase XVI: vLLM Server Startup Script
# Starts a vLLM server with continuous batching for the Infinite Context RAG engine.
# ─────────────────────────────────────────────────────────────────────────────
#
# REQUIREMENTS: pip install vllm
# HARDWARE: RTX 5070 (12GB VRAM) — adjust --max-model-len if you run out of VRAM
#
# HOW TO USE:
#   1. bash vllm_server.sh
#   2. In another terminal: python src/memory_engine_vllm.py
#
# ─────────────────────────────────────────────────────────────────────────────

MODEL=${VLLM_MODEL:-"deepseek-ai/DeepSeek-R1-Distill-Llama-8B"}
PORT=${VLLM_PORT:-8000}
GPU_UTIL=${VLLM_GPU_UTIL:-0.85}    # Use 85% of VRAM — leave headroom for embeddings
MAX_LEN=${VLLM_MAX_LEN:-4096}
DTYPE=${VLLM_DTYPE:-"half"}        # float16 for RTX 5070

echo "─────────────────────────────────────────────────────────────────────────────"
echo "🚀 PHASE XVI: Starting vLLM Server"
echo "   Model:       $MODEL"
echo "   Port:        $PORT"
echo "   GPU Util:    $GPU_UTIL"
echo "   Max ctx len: $MAX_LEN"
echo "─────────────────────────────────────────────────────────────────────────────"

# Wait for GPU to be free
sleep 2

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --dtype "$DTYPE" \
    --gpu-memory-utilization "$GPU_UTIL" \
    --max-model-len "$MAX_LEN" \
    --enable-chunked-prefill \
    --max-num-batched-tokens "$MAX_LEN" \
    --trust-remote-code
