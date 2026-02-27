import os
import sys
import uuid
import threading
import warnings
import logging
import time
import json
import asyncio
import aiohttp
from openai import OpenAI
import requests

# Silence all logging/warnings
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)

import chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATION ---
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "news_memory_v2" 

# Local LM Studio Server
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"

# --- GLOBAL CLIENTS ---
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

local_client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key="lm-studio")

class TruncatedEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, base_ef, dimensions=256):
        self.base_ef = base_ef
        self.dimensions = dimensions

    def __call__(self, input):
        try:
            embeddings = self.base_ef(input)
            return [emb[:self.dimensions] for emb in embeddings]
        except Exception as e:
            print(f"      [Embedding Error] {e}")
            return [[0.0] * self.dimensions for _ in input]


class LMStudioEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, url="http://localhost:1234/v1/embeddings"):
        self.url = url
        
    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        payload = {"model": "text-embedding-nomic-embed-text-v1.5@f32", "input": input}
        try:
            resp = requests.post(self.url, json=payload, timeout=20)
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]
        except Exception as e:
            print(f"      [Local Embed Error] {e}")
            return [[0.0] * 2048 for _ in input]

def get_collection():
    """Returns the ChromaDB collection using embedded DB and Truncated Local Embeddings."""
    base_ef = LMStudioEmbeddingFunction(url=f"{LM_STUDIO_BASE_URL}/embeddings")
    truncated_ef = TruncatedEmbeddingFunction(base_ef, dimensions=256)
    
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=truncated_ef
    )

# --- ASYNC EXTRACTION ---
# Since LM Studio handles multiple parallel requests slower than OpenRouter, drop concurrency slightly
extraction_semaphore = asyncio.Semaphore(2) 

async def async_extract_chunk(session, chunk_text, question, chunk_idx):
    extraction_prompt = f"Context: {chunk_text}\nQuestion: {question}\nExtract relevant parts verbatim, or say NOT_FOUND."
    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "messages": [{"role": "user", "content": extraction_prompt}],
        "temperature": 0.0
    }
    url = f"{LM_STUDIO_BASE_URL}/chat/completions"
    async with extraction_semaphore:
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if result and "NOT_FOUND" not in result:
                        return f"[Chunk {chunk_idx}]: {result}"
        except: pass
        return None

async def async_parallel_extract(raw_context, question):
    pages = [raw_context[i:i+4000] for i in range(0, len(raw_context), 4000)]
    if len(pages) <= 1: return None
    
    print(f"   [Local Extract] Firing {len(pages)} local workers...")
    async with aiohttp.ClientSession() as session:
        tasks = [async_extract_chunk(session, p, question, i) for i, p in enumerate(pages)]
        results = await asyncio.gather(*tasks)
    
    findings = [r for r in results if r]
    return "\n".join(findings) if findings else None

def chat_logic(user_input):
    collection = get_collection()
    
    # 1. Local Search 
    results = collection.query(query_texts=[user_input[:500]], n_results=6)
    memories = results['documents'][0] if results['documents'] else []
    
    # Label the top candidates for the AI
    formatted_candidates = []
    for i, m in enumerate(memories):
        label = f"[Candidate {i+1}]"
        formatted_candidates.append(f"{label}\n{m}")
    
    # Cap the raw context at 10000 characters
    raw_context = "\n---\n".join(formatted_candidates)[:10000]
    print(f"   [Logic] Found {len(memories)} local candidate documents.")
    
    # 2. Local Extraction (Optional context condensing)
    extraction_findings = ""
    if len(raw_context) > 4000:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            extraction_findings = loop.run_until_complete(async_parallel_extract(raw_context, user_input))
            loop.close()
        except: pass

    # 3. Final Local Reasoning
    context = extraction_findings if extraction_findings else raw_context
    system_prompt = f"""You are InfiniteMemory, an elite AI specialized in exact retrieval and deep analysis.
Your primary job is to answer the user's question strictly and accurately based on the provided Context.

The Context is presented as multiple [Candidate] blocks. These are ranked by initial retrieval relevance:
- examine all Candidates carefully.
- If Candidate 1 doesn't have the answer, check Candidate 2, and so on.
- Some candidates might be similar topics but incorrect details; be precise.
- If the answer is not in the Context, you must explicitly state that you do not know. 
- Do not hallucinate or make up information.

Context:
{context}
"""
    
    print(f"   [Logic] Sending reasoning request to LM Studio...")
    
    response = local_client.chat.completions.create(
        model="deepseek/deepseek-r1-0528-qwen3-8b",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
        temperature=0.0
    )
    answer = response.choices[0].message.content
    
    # Extract Usage Metrics for Token Counter UI
    usage_dict = response.usage.model_dump() if response.usage else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 4. Background Save 
    def _save():
        try:
            combined = f"U: {user_input}\nAI: {answer}"
            payload = {"model": "text-embedding-nomic-embed-text-v1.5@f32", "input": combined}
            emb_resp = requests.post(f"{LM_STUDIO_BASE_URL}/embeddings", json=payload).json()
            
            if "data" in emb_resp and len(emb_resp["data"]) > 0:
                truncated_emb = emb_resp["data"][0]["embedding"][:256]
                collection.add(documents=[combined], embeddings=[truncated_emb], ids=[str(uuid.uuid4())])
        except Exception as e: 
            print(f"   [Save Error] {e}")
            
    threading.Thread(target=_save).start()

    return answer, {"status": "success", "usage": usage_dict}

if __name__ == "__main__":
    ans, metrics = chat_logic("Tell me about Nathan Lyon.")
    print(f"\nAI: {ans}")
    print(f"Metrics: {metrics}")
