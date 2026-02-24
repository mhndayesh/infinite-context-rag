"""
Phase XVI Benchmark: Ollama vs vLLM Async Extraction
─────────────────────────────────────────────────────
Compares extraction speed between:
  A) Ollama   (serial queue, baseline)
  B) vLLM     (continuous batching, true parallel)

USAGE:
  1. Start vLLM server:
       python -m vllm.entrypoints.openai.api_server \
           --model deepseek-ai/DeepSeek-R1-Distill-Llama-8B \
           --port 8000 --gpu-memory-utilization 0.80
     OR just run:  bash ../vllm_server.sh

  2. Run this benchmark:
       python benchmarks/phase16_benchmark.py
"""

import sys, os, time, json, shutil, uuid, asyncio

# Point to the Phase XVI engine
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import memory_engine_vllm as engine

ESSAYS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'experiment_9_needle_in_haystack', 'dataset_repo', 'needlehaystack', 'PaulGrahamEssays'
)
NEEDLE   = "The secret magical password to unlock the core mainframe is ALBATROSS-9000."
QUESTION = "What is the secret password to unlock the core mainframe?"
EXPECTED = "ALBATROSS-9000"
DB_PATH  = "./temp_phase16_db"
CHUNK_SIZE = 2000
TARGET_CHARS = 32000 * 4  # 32k tokens ≈ 128k chars


def load_essays():
    text = ""
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
        shutil.rmtree(DB_PATH)

    emb_fn = embedding_functions.OllamaEmbeddingFunction(
        model_name=engine.EMBED_MODEL,
        url="http://localhost:11434/api/embeddings"
    )
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.create_collection(
        "raw_history", embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Insert needle at 25% depth
    pos = len(haystack_text) // 4
    while pos < len(haystack_text) and haystack_text[pos] != '.':
        pos += 1
    full = haystack_text[:pos+1] + " " + NEEDLE + " " + haystack_text[pos+1:]

    chunks = [full[i:i+CHUNK_SIZE] for i in range(0, len(full), CHUNK_SIZE)]
    group_id = str(uuid.uuid4())
    print(f"   Embedding {len(chunks)} chunks (32k tokens)...")

    for i in range(0, len(chunks), 10):
        batch = chunks[i:i+10]
        metas = [{"type": "FACT", "group_id": group_id, "chunk_index": i+j,
                  "total_chunks": len(chunks), "entities": ""} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        collection.add(documents=batch, metadatas=metas, ids=ids)

    # Inject into engine globals
    engine._client = client
    engine._collection = collection
    engine.DB_PATH = DB_PATH
    engine.rolling_chat_buffer = []
    engine.session_chunk_index = 0
    print(f"   DB ready: {collection.count()} chunks.")
    return collection.count()


def run(label, async_enabled, engine_url):
    engine.ASYNC_EXTRACTION_ENABLED = async_enabled
    engine.VLLM_URL = engine_url
    engine.sync_global_bm25(force=True)
    engine.rolling_chat_buffer = []

    t = time.perf_counter()
    answer, timings = engine.chat_logic(QUESTION)
    total = time.perf_counter() - t
    passed = EXPECTED.lower() in answer.lower()

    print(f"\n[{label}]")
    print(f"  Retrieval : {timings['retrieval']:.2f}s")
    print(f"  Inference : {timings['inference']:.2f}s")
    print(f"  Total     : {total:.2f}s")
    print(f"  PASS      : {passed}")
    print(f"  Answer    : {answer[:120]}")
    return {"label": label, "retrieval": timings['retrieval'],
            "inference": timings['inference'], "total": total, "pass": passed}


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE XVI BENCHMARK: Ollama vs vLLM Async Extraction")
    print("=" * 60)

    print("\nLoading essays...")
    haystack = load_essays()
    setup_db(haystack)

    results = []

    # A: Baseline — Ollama, async OFF
    results.append(run("OLLAMA  (ASYNC OFF)", False, ""))

    engine.rolling_chat_buffer = []

    # B: Ollama async ON (Phase XV — serial queue, should be slower on extraction)
    engine.OLLAMA_HTTP_URL = "http://localhost:11434/api/chat"
    results.append(run("OLLAMA  (ASYNC ON) ", True, ""))

    engine.rolling_chat_buffer = []

    # C: vLLM async ON (Phase XVI — true GPU parallel, should be fastest)
    results.append(run("vLLM    (ASYNC ON) ", True, "http://localhost:8000/v1"))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Engine':<25} {'Total':>8}  {'PASS':>6}")
    print("-" * 42)
    for r in results:
        print(f"{r['label']:<25} {r['total']:>7.1f}s  {'✅' if r['pass'] else '❌':>5}")

    # Save results
    os.makedirs("../results", exist_ok=True)
    with open("../results/phase16_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to results/phase16_benchmark.json")

    shutil.rmtree(DB_PATH, ignore_errors=True)
