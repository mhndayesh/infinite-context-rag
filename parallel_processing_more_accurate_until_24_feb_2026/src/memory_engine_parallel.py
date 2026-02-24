import sys, os, time, json, shutil, uuid, asyncio, re, warnings
import datetime
from typing import List, Optional

# Phase XVI: Parallel Engine for OpenAI-compatible Servers (LM Studio / vLLM / Aphrodite)
import aiohttp
from openai import AsyncOpenAI
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

# Force parallel extraction for Phase XVI
ASYNC_EXTRACTION_ENABLED = True
EXTRACTION_PAGE_SIZE = 1500

# CONFIG: Set this to your LM Studio / vLLM URL
OPENAI_API_BASE = "http://localhost:8000/v1" # vLLM default
OPENAI_API_KEY = "vllm-key"
LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
EMBED_MODEL = "nomic-embed-text"
DB_PATH = "./memory_db"

# --- Globals ---
_client = None
_collection = None
global_bm25 = None
global_corpus_docs = []
global_corpus_ids = []
global_corpus_metas = []
bm25_last_sync_time = 0
rolling_chat_buffer = []

# Initialize Async client
async_openai = AsyncOpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_API_KEY)

async def async_extract_chunk(chunk: str, question: str) -> Optional[str]:
    """Sends a single chunk to the parallel server for fact extraction."""
    system_prompt = f"""You are a Parallel Fact Extractor.
Task: Identify ONLY the specific fact or answer to the question within the provided context.
Output format: [FACT: description] or NOT_FOUND. NO explanation.

Question: "{question}" """
    
    try:
        response = await async_openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{chunk}"}
            ],
            temperature=0.0,
            max_tokens=200
        )
        ans = response.choices[0].message.content.strip()
        if "NOT_FOUND" in ans or len(ans) < 5:
            return None
        return ans
    except Exception as e:
        print(f"      [Worker Error] {e}")
        return None

async def async_parallel_extract(context: str, question: str) -> Optional[str]:
    """Splits context and fires parallel workers via asyncio.gather."""
    # Split into fixed-size pages
    pages = [context[i:i+EXTRACTION_PAGE_SIZE] for i in range(0, len(context), EXTRACTION_PAGE_SIZE)]
    print(f"   [Phase XVI] MAP: Firing {len(pages)} extraction workers in parallel (LM Studio/vLLM)...")
    
    start_t = time.perf_counter()
    tasks = [async_extract_chunk(p, question) for p in pages]
    results = await asyncio.gather(*tasks)
    
    # REDUCE: Filter out None and deduplicate
    findings = [r for r in results if r]
    elapsed = time.perf_counter() - start_t
    
    if not findings:
        return None
        
    cheat_sheet = f"--- [RELEVANT EXTRACTS - PARALLEL] ---\n" + "\n".join(findings) + "\n-----------------------------------"
    print(f"   [Phase XVI] REDUCE: {len(findings)}/{len(pages)} chunks yielded facts. ({elapsed:.2f}s total)")
    return cheat_sheet

# --- Core RAG Logic (Simplified for Benchmark) ---

def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=DB_PATH)
        emb_fn = embedding_functions.OllamaEmbeddingFunction(model_name=EMBED_MODEL, url="http://localhost:11434/api/embeddings")
        _collection = _client.get_or_create_collection("raw_history", embedding_function=emb_fn)
    return _collection

def sync_global_bm25(force=False):
    """Refreshes the global BM25 index from ChromaDB."""
    global global_bm25, global_corpus_docs, global_corpus_ids, global_corpus_metas, bm25_last_sync_time
    
    collection = get_collection()
    count = collection.count()
    if count == 0: return

    # Simple throttle
    if not force and count == len(global_corpus_docs) and (time.time() - bm25_last_sync_time) < 60:
        return
        
    try:
        all_data = collection.get(include=['documents', 'metadatas'])
        global_corpus_docs = all_data['documents']
        global_corpus_ids = all_data['ids']
        global_corpus_metas = all_data['metadatas']
        tokenized_docs = [doc.split() for doc in global_corpus_docs]
        global_bm25 = BM25Okapi(tokenized_docs)
        bm25_last_sync_time = time.time()
        print(f"   [BM25 Sync] Re-indexed {count} chunks.")
    except Exception as e:
        print(f"   [BM25 Sync] Error: {e}")

async def chat_logic_async(user_input: str):
    start_total = time.perf_counter()
    
    # 1. Hybrid Retrieval
    sync_global_bm25()
    collection = get_collection()
    
    # Path A: Vector
    vector_results = collection.query(query_texts=[user_input], n_results=10)
    v_ids = vector_results['ids'][0] if vector_results['ids'] else []
    
    # Path B: BM25
    b_ids = []
    if global_bm25:
        query_tokens = user_input.lower().split()
        scores = global_bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:10]
        b_ids = [global_corpus_ids[i] for i in top_indices if scores[i] > 0]

    # RRF Merge
    rrf_scores = {}
    for rank, cid in enumerate(v_ids): rrf_scores[cid] = rrf_scores.get(cid, 0) + 1/(60 + rank + 1)
    for rank, cid in enumerate(b_ids): rrf_scores[cid] = rrf_scores.get(cid, 0) + 1/(60 + rank + 1)
    
    sorted_hits = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    doc_hits = []
    for cid, _ in sorted_hits:
        idx = global_corpus_ids.index(cid)
        doc_hits.append(global_corpus_docs[idx])
        
    retrieval_t = time.perf_counter() - start_total
    print(f"   [RAG Stage 1] Found {len(doc_hits)} hits. ({retrieval_t:.2f}s)")

    # 2. Parallel Extraction (Phase XVI)
    raw_context = "\n---\n".join(doc_hits)
    cheat_sheet = ""
    if ASYNC_EXTRACTION_ENABLED and len(raw_context) > 2000:
        cheat_sheet = await async_parallel_extract(raw_context, user_input)
    
    # 3. Final Answer
    prompt = f"""Answer the question based on the context. If a cheat sheet is provided, use it for facts.
Question: "{user_input}"
Context:
{cheat_sheet if cheat_sheet else ""}
{raw_context}
"""
    
    start_inf = time.perf_counter()
    response = await async_openai.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    inference_t = time.perf_counter() - start_inf
    
    return answer, {"retrieval": retrieval_t, "inference": inference_t}

def chat_logic(user_input):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(chat_logic_async(user_input))
    loop.close()
    return res
