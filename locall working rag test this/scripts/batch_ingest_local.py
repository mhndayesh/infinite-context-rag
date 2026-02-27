import os
import glob
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import requests

import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)

import chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATION ---
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "news_memory_v2"
DATA_DIR = "./data"
LM_STUDIO_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5@f32"

CHUNK_SIZE = 2000     # characters (~1500 tokens)
CHUNK_OVERLAP = 500   # character overlap to preserve semantic flow
BATCH_SIZE = 1000      # ABSOLUTE LIMIT: 1000 chunks per call
MAX_CONCURRENCY = 8    # Saturated Parallel Waves

# --- EMBEDDING ENGINE ---
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
    def __init__(self, url):
        self.url = url
        
    def __call__(self, input):
        if isinstance(input, str): input = [input]
        payload = {"model": EMBED_MODEL, "input": input}
        try:
            resp = requests.post(self.url, json=payload, timeout=30)
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]
        except Exception:
            return [[0.0] * 2048 for _ in input]

# Setup DB
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
base_ef = LMStudioEmbeddingFunction(url=LM_STUDIO_URL)
truncated_ef = TruncatedEmbeddingFunction(base_ef, dimensions=256)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=truncated_ef)

# --- CHUNKING LOGIC ---
def process_file(file_path):
    print(f"\n📂 Reading: {os.path.basename(file_path)}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        print(f"⚠️ Skipping {os.path.basename(file_path)} - Not valid UTF-8 text.")
        return []

    if not text.strip(): return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (CHUNK_SIZE - CHUNK_OVERLAP)

    print(f"   => Sliced into {len(chunks)} overlapping chunks.")
    return chunks

# --- BATCHED INGESTION ---
def ingest_batch(batch_chunks):
    try:
        payload = {"model": EMBED_MODEL, "input": batch_chunks}
        # Huge timeout for 1000-chunk batches
        resp = requests.post(LM_STUDIO_URL, json=payload, timeout=300).json()
        if "data" in resp:
            embeddings = [item["embedding"][:256] for item in resp["data"]]
            collection.add(
                documents=batch_chunks,
                embeddings=embeddings,
                ids=[str(uuid.uuid4()) for _ in range(len(batch_chunks))]
            )
            return len(batch_chunks)
    except Exception as e:
        print(f"   [Limit Error] {e}")
    return 0

def main():
    print("="*60)
    print("🚀 MAX-SPEED TURBO-CHARGED INGESTION STARTING")
    print("="*60)
    
    file_paths = glob.glob(os.path.join(DATA_DIR, "**", "*.*"), recursive=True)
    txt_files = [f for f in file_paths if f.endswith('.txt') or f.endswith('.md')]
    
    if not txt_files:
        print(f"❌ No files found in {os.path.abspath(DATA_DIR)}")
        return

    all_chunks = []
    for f in txt_files:
        all_chunks.extend(process_file(f))

    if not all_chunks: return

    # Create batches
    batches = [all_chunks[i:i + BATCH_SIZE] for i in range(0, len(all_chunks), BATCH_SIZE)]
    total_batches = len(batches)
    
    print(f"\n🔥 Commencing MAX-LIMIT Multi-Threaded Ingestion (Batches: {total_batches})")
    print(f"🎯 Target: {LM_STUDIO_URL} (Threads: {MAX_CONCURRENCY}, Batch Size: {BATCH_SIZE})")
    
    start_time = time.time()
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        futures = {executor.submit(ingest_batch, b) for b in batches}
        for future in tqdm(as_completed(futures), total=total_batches, desc="Turbo Ingesting"):
            success_count += future.result()
                
    elapsed = time.time() - start_time
    print("="*60)
    print(f"✅ ULTRA-FAST INGESTION COMPLETE")
    print(f"⏱️ Time Taken: ..... {elapsed:.2f} seconds")
    print(f"💾 Total Saved: ... {success_count}/{len(all_chunks)} chunks inserted.")
    print("="*60)

if __name__ == "__main__":
    main()
    print("Ready for local retrieval via the Offline UI!")
