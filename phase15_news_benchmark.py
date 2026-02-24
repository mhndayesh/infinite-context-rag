"""
Phase XV News DB Benchmark
Tests async parallel extraction with dense, multi-page context using
Paul Graham essays as the "news" haystack (same corpus as NIAH).
"""
import sys
import os
import uuid
import time
import shutil
import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiment_5_phi4mini_baseline'))
import memory_engine

# ─── Config ───────────────────────────────────────────────────────────────────
ESSAYS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiment_9_needle_in_haystack', 'dataset_repo', 'needlehaystack', 'PaulGrahamEssays')
NEEDLE = "The secret magical password to unlock the core mainframe is ALBATROSS-9000."
QUESTION = "What is the secret password to unlock the core mainframe?"
EXPECTED = "ALBATROSS-9000"
TARGET_TOKENS = 32000   # 32k tokens = ~128k chars — large enough for multi-page extraction
DB_PATH = "./temp_news_test_db"
CHUNK_SIZE = 2000

def load_essays():
    text = ""
    for fn in os.listdir(ESSAYS_DIR):
        if fn.endswith(".txt"):
            with open(os.path.join(ESSAYS_DIR, fn), encoding='utf-8') as f:
                text += f.read() + "\n\n"
    # Repeat until we have enough
    while len(text) < TARGET_TOKENS * 4:
        text += text
    return text[:TARGET_TOKENS * 4]

def setup_db(haystack_text):
    """Wipe and re-create an isolated DB with the news haystack."""
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
    
    emb_fn = embedding_functions.OllamaEmbeddingFunction(
        model_name=memory_engine.EMBED_MODEL,
        url="http://localhost:11434/api/embeddings"
    )
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.create_collection("raw_history", embedding_function=emb_fn, metadata={"hnsw:space": "cosine"})
    
    # Insert needle at the 25% depth mark
    insert_idx = len(haystack_text) // 4
    while insert_idx < len(haystack_text) and haystack_text[insert_idx] != '.':
        insert_idx += 1
    haystack_with_needle = haystack_text[:insert_idx+1] + " " + NEEDLE + " " + haystack_text[insert_idx+1:]
    
    chunks = [haystack_with_needle[i:i+CHUNK_SIZE] for i in range(0, len(haystack_with_needle), CHUNK_SIZE)]
    group_id = str(uuid.uuid4())
    batch_size = 10
    print(f"   Embedding {len(chunks)} chunks (~{TARGET_TOKENS//1000}k tokens)...")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        metas = [{"type": "FACT", "group_id": group_id, "chunk_index": i+j, "total_chunks": len(chunks), "entities": ""} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        collection.add(documents=batch, metadatas=metas, ids=ids)

    # Inject db into memory_engine
    memory_engine._client = client
    memory_engine._collection = collection
    memory_engine.DB_PATH = DB_PATH
    memory_engine.rolling_chat_buffer = []
    memory_engine.session_chunk_index = 0
    print(f"   DB ready: {collection.count()} chunks.")
    return collection.count()

def run_test(async_enabled):
    tag = "ASYNC ON " if async_enabled else "ASYNC OFF"
    memory_engine.ASYNC_EXTRACTION_ENABLED = async_enabled
    memory_engine.sync_global_bm25(force=True)

    t = time.perf_counter()
    answer, timings = memory_engine.chat_logic(QUESTION)
    total = time.perf_counter() - t

    passed = EXPECTED.lower() in answer.lower().replace('.', '').replace(',', '')
    print(f"\n[{tag}] Retrieval: {timings['retrieval']:.2f}s | Inference: {timings['inference']:.2f}s | Total: {total:.2f}s")
    print(f"[{tag}] PASS={passed} | Answer snippet: {answer[:120]}")
    return total, passed

if __name__ == "__main__":
    print("=== PHASE XV: NEWS HAYSTACK BENCHMARK ===")
    print(f"Loading Paul Graham essays (~{TARGET_TOKENS//1000}k tokens)...")
    haystack = load_essays()
    chunk_count = setup_db(haystack)
    print(f"\nRunning queries on {chunk_count} chunks...\n")

    total_async, pass_async = run_test(async_enabled=True)
    print("Resetting buffer for baseline run...")
    memory_engine.rolling_chat_buffer = []
    total_seq, pass_seq = run_test(async_enabled=False)

    print(f"\n{'─'*50}")
    print(f"ASYNC ON:  {total_async:.1f}s — PASS={pass_async}")
    print(f"ASYNC OFF: {total_seq:.1f}s   — PASS={pass_seq}")
    print(f"Time saved: {total_seq - total_async:.1f}s")

    # Cleanup
    memory_engine._client = None
    memory_engine._collection = None
    shutil.rmtree(DB_PATH, ignore_errors=True)
