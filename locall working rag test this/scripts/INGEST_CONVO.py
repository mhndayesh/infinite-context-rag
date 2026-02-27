import os
import sys
import uuid
import time
import concurrent.futures
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

# Ensure we can import the engine config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import memory_engine_parallel_lms as engine

DATASET_PATH = r"c:\new-ai,arch\archive\512k_window_evaluation\dataset512k"
CHUNK_SIZE = 6000 
CHUNK_OVERLAP = 500
MAX_EMBED_WORKERS = 64

# Smart Splitter: Keeps paragraphs and sentences together
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    is_separator_regex=False,
)

# Initialize OpenRouter client for parallel embedding fetching
client_or = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=engine.OPENROUTER_API_KEY,
)

def fetch_embedding(text):
    """Fetches a single embedding directly from OpenRouter."""
    try:
        response = client_or.embeddings.create(input=text, model=engine.EMBED_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"      [Parallel Error] Embedding fetch failed: {e}")
        return None

def process_and_save_batch(collection, batch_docs, batch_metas, batch_ids):
    """Helper to fetch embeddings in parallel and save to ChromaDB."""
    if not batch_docs:
        return 0
    
    print(f"      [Parallel] Fetching {len(batch_docs)} embeddings with {MAX_EMBED_WORKERS} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_EMBED_WORKERS) as executor:
        batch_embeddings = list(executor.map(fetch_embedding, batch_docs))
    
    # Filter out any failed embeddings
    valid_docs, valid_embeds, valid_metas, valid_ids = [], [], [], []
    for doc, embed, meta, id in zip(batch_docs, batch_embeddings, batch_metas, batch_ids):
        if embed is not None:
            valid_docs.append(doc)
            valid_embeds.append(embed)
            valid_metas.append(meta)
            valid_ids.append(id)
    
    # Truncate for Matryoshka efficiency (Nomic supports this)
    # We slice 768 down to 256
    truncated_embeds = [emb[:256] for emb in valid_embeds]
    
    if valid_docs:
        collection.add(
            documents=valid_docs,
            embeddings=truncated_embeds,
            metadatas=valid_metas,
            ids=valid_ids
        )
    return len(valid_docs)

def ingest_conversational_data():
    collection = engine.get_collection()
    
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Error: Dataset path not found: {DATASET_PATH}")
        return

    files = [f for f in os.listdir(DATASET_PATH) if f.endswith('.txt')]
    print(f"🚀 Found {len(files)} files. Starting HIGH-SPEED parallel ingestion...")
    
    total_chunks = 0
    start_time = time.time()

    for filename in files:
        filepath = os.path.join(DATASET_PATH, filename)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"\n📄 Processing: {filename} ({file_size_mb:.1f} MB)...")
        
        group_id = str(uuid.uuid4())
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Recursive Smart Slicing
            chunks = text_splitter.split_text(content)
            print(f"   -> Sliced into {len(chunks)} smart chunks (overlap: {CHUNK_OVERLAP}).")
            
            batch_docs, batch_metas, batch_ids = [], [], []
            
            for idx, chunk in enumerate(chunks):
                convo_text = f"U: I have some news data from {filename}:\n{chunk.strip()}\nAI: Understood. I've committed this information about {filename} to my memory."
                
                batch_docs.append(convo_text)
                batch_metas.append({
                    "type": "FACT", 
                    "group_id": group_id, 
                    "chunk_index": idx,
                    "source": filename
                })
                batch_ids.append(str(uuid.uuid4()))
                
                if len(batch_docs) >= 200:
                    saved_count = process_and_save_batch(collection, batch_docs, batch_metas, batch_ids)
                    total_chunks += saved_count
                    batch_docs, batch_metas, batch_ids = [], [], []
                    print(f"      [Progress] {total_chunks} total chunks ingested...")

            # Add remaining chunks for this file
            if batch_docs:
                saved_count = process_and_save_batch(collection, batch_docs, batch_metas, batch_ids)
                total_chunks += saved_count
            
            print(f"   ✅ Finished {filename}. Total chunks so far: {total_chunks}")
            
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")

    duration = time.time() - start_time
    print(f"\n✨ SUCCESS: Ingested {total_chunks} chunks as conversations.")
    print(f"   Total time: {duration/60:.2f} minutes.")
    print(f"   Collection count: {collection.count()}")


if __name__ == "__main__":
    ingest_conversational_data()
