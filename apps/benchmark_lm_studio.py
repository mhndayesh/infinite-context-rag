"""
LM Studio Benchmark: Needle-in-a-Haystack (NIAH)
────────────────────────────────────────────────
Evaluates the refactored memory_engine.py using LM Studio.

USAGE:
  1. Start LM Studio server at http://127.0.0.1:1234
  2. python plug_and_play/benchmark_lm_studio.py
"""

import os
import time
import json
import shutil
import uuid
import sys

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import memory_engine_parallel_lms as engine

ESSAYS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'experiment_9_needle_in_haystack', 'dataset_repo', 'needlehaystack', 'PaulGrahamEssays'
)
NEEDLE   = "The secret magical password to unlock the core mainframe is ALBATROSS-9000."
QUESTION = "What is the secret password to unlock the core mainframe?"
EXPECTED = "ALBATROSS-9000"
DB_PATH  = "./temp_lm_studio_db"
CHUNK_SIZE = 2000
TARGET_CHARS = 2000000  # ≈ 512k tokens

def load_essays():
    text = ""
    if not os.path.exists(ESSAYS_DIR):
        print(f"Error: Essays directory not found at {ESSAYS_DIR}")
        return "Standard placeholder text. " * 80000
        
    for fn in os.listdir(ESSAYS_DIR):
        if fn.endswith(".txt"):
            with open(os.path.join(ESSAYS_DIR, fn), encoding='utf-8') as f:
                text += f.read() + "\n\n"
    while len(text) < TARGET_CHARS:
        text += text
    return text[:TARGET_CHARS]

def setup_db(haystack_text):
    import chromadb
    from chromadb.utils import embedding_functions

    if os.path.exists(DB_PATH):
        try:
            shutil.rmtree(DB_PATH)
        except:
            pass

    # Update engine config for benchmark
    engine.DB_PATH = DB_PATH
    
    # Force re-initialization of collection with benchmark DB path
    engine._client = None
    engine._collection = None
    collection = engine.get_collection()

    # Insert needle at 50% depth
    pos = len(haystack_text) // 2
    while pos < len(haystack_text) and haystack_text[pos] != '.':
        pos += 1
    full = haystack_text[:pos+1] + " " + NEEDLE + " " + haystack_text[pos+1:]

    chunks = [full[i:i+CHUNK_SIZE] for i in range(0, len(full), CHUNK_SIZE)]
    group_id = str(uuid.uuid4())
    print(f"   Embedding {len(chunks)} chunks (512k tokens)...")

    # Batch embedding for speed (Batch of 20)
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        metas = [{"type": "FACT", "group_id": group_id, "chunk_index": i+j,
                  "total_chunks": len(chunks), "entities": ""} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        try:
            collection.add(documents=batch, metadatas=metas, ids=ids)
        except Exception as e:
            print(f"Error adding batch at {i}: {e}")

    print(f"   DB ready: {collection.count()} chunks.")
    return collection

def run_benchmark():
    print("=" * 60)
    print("LM STUDIO BENCHMARK: Needle-in-a-Haystack")
    print("=" * 60)

    print("\nLoading essays...")
    haystack = load_essays()
    setup_db(haystack)

    print(f"\nRunning Query: '{QUESTION}'")
    t = time.perf_counter()
    answer, timings = engine.chat_logic(QUESTION)
    total = time.perf_counter() - t
    passed = EXPECTED.lower() in answer.lower()

    print(f"\n[RESULTS]")
    print(f"  Retrieval : {timings['retrieval']:.2f}s")
    print(f"  Inference : {timings['inference']:.2f}s")
    print(f"  Total     : {total:.2f}s")
    print(f"  PASS      : {'✅ YES' if passed else '❌ NO'}")
    print(f"  Answer    : {answer.strip()}")
    
    # Save results
    results = {
        "engine": "LM Studio",
        "retrieval_s": timings['retrieval'],
        "inference_s": timings['inference'],
        "total_s": total,
        "pass": passed,
        "answer": answer
    }
    
    os.makedirs("results", exist_ok=True)
    with open("results/lm_studio_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to results/lm_studio_benchmark.json")

    # Clean up
    try:
        shutil.rmtree(DB_PATH, ignore_errors=True)
    except:
        pass

if __name__ == "__main__":
    run_benchmark()
