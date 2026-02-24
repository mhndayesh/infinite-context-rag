"""
🚀 Phase XVI: High-Precision Parallel News Benchmark
═══════════════════════════════════════════════════════
Tests the 16-slot parallel engine and Direct-Return bypass
at 512k scale using Paul Graham essays as the noise corpus.
"""

import sys
import os
import uuid
import time
import shutil
import chromadb
from chromadb.utils import embedding_functions
import asyncio

# Ensure we can import the Phase 16 engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_engine_parallel_lms as engine

# ─── Config ───────────────────────────────────────────────────────────────────
ESSAYS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiment_9_needle_in_haystack', 'dataset_repo', 'needlehaystack', 'PaulGrahamEssays')
NEEDLE = "The secret magical password to unlock the core mainframe is ALBATROSS-9000."
QUESTION = "What is the secret password to unlock the core mainframe?"
EXPECTED = "ALBATROSS-9000"
TARGET_TOKENS = 512000  # Full NIAH Scale
DB_PATH = "./temp_phase16_benchmark_db"
CHUNK_SIZE = 2000

def load_essays():
    if not os.path.exists(ESSAYS_DIR):
        print(f"❌ Error: {ESSAYS_DIR} not found.")
        return "Generic noise text. " * 50000
    
    text = ""
    for fn in os.listdir(ESSAYS_DIR):
        if fn.endswith(".txt"):
            with open(os.path.join(ESSAYS_DIR, fn), encoding='utf-8') as f:
                text += f.read() + "\n\n"
    
    # Scale up to 512k tokens (~2M chars)
    while len(text) < TARGET_TOKENS * 4:
        text += text
    return text[:TARGET_TOKENS * 4]

def setup_db(haystack_text):
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
    
    # Use Phase 16 engine's embedding logic
    emb_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key="lm-studio",
        api_base=engine.LM_STUDIO_URL,
        model_name=engine.EMBED_MODEL
    )
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.create_collection("raw_history", embedding_function=emb_fn)
    
    # Inject needle
    insert_idx = len(haystack_text) // 2
    haystack_with_needle = haystack_text[:insert_idx] + " " + NEEDLE + " " + haystack_text[insert_idx:]
    
    chunks = [haystack_with_needle[i:i+CHUNK_SIZE] for i in range(0, len(haystack_with_needle), CHUNK_SIZE)]
    print(f"   Indexing {len(chunks)} chunks...")
    
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        metas = [{"source": "benchmark", "chunk": i+j} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        collection.add(documents=batch, metadatas=metas, ids=ids)
    
    # Point engine to this benchmark DB
    engine.DB_PATH = DB_PATH
    engine._client = client
    engine._collection = collection
    print(f"   ✅ Benchmark DB ready: {collection.count()} chunks.")

async def run_benchmark():
    print(f"\n--- Starting Phase 16 Parallel Benchmark ---")
    print(f"Goal: Extract '{EXPECTED}' from {TARGET_TOKENS} tokens of noise.")
    
    start_t = time.perf_counter()
    answer, timings = await engine.chat_logic_async(QUESTION)
    total = time.perf_counter() - start_t
    
    passed = EXPECTED.lower() in answer.lower()
    print(f"\n[PHASE 16] Result: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"[PHASE 16] Total Time: {total:.2f}s")
    print(f"[PHASE 16] Retrieval: {timings['retrieval']:.2f}s")
    print(f"[PHASE 16] Answer: {answer}")

if __name__ == "__main__":
    print("🚀 LOADING HAYSTACK...")
    haystack = load_essays()
    setup_db(haystack)
    
    asyncio.run(run_benchmark())
    
    # Cleanup
    shutil.rmtree(DB_PATH, ignore_errors=True)
