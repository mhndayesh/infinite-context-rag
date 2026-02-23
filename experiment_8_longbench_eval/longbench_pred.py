import os
import sys
import json
import time
import shutil
import uuid
import re
from tqdm import tqdm
from datasets import load_dataset
from chromadb.utils import embedding_functions
import chromadb

# Import the exact memory engine we used in Exp 5
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'experiment_5_phi4mini_baseline')))
import memory_engine

# Silence noisy libraries
import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)

DB_BASE_DIR = os.path.join(os.path.dirname(__file__), 'temp_longbench_dbs')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def cleanup_db(db_path):
    """Force remove a ChromaDB directory and its locks."""
    try:
        if os.path.exists(db_path):
            shutil.rmtree(db_path, ignore_errors=True)
            # Second pass for tenacious sqlite locks
            if os.path.exists(db_path):
                time.sleep(1)
                shutil.rmtree(db_path, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not clean {db_path}: {e}")

def create_isolated_memory(item_id, context_text):
    """
    Creates a fresh ChromaDB instance JUST for this single LongBench question,
    embeds the massive context, and points memory_engine.py to it.
    """
    db_path = os.path.join(DB_BASE_DIR, f"db_{item_id}")
    cleanup_db(db_path)
    os.makedirs(db_path, exist_ok=True)
    
    # 1. Initialize isolated Chroma Client
    emb_fn = embedding_functions.OllamaEmbeddingFunction(
        model_name=memory_engine.EMBED_MODEL,
        url="http://localhost:11434/api/embeddings",
    )
    client = chromadb.PersistentClient(path=db_path)
    collection = client.create_collection(
        name="raw_history",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 2. Chunk and Embed the Long Context (bypassing slow LLM classifier)
    # LongBench contexts are 8k to 2M words. We use large 2000-char chunks.
    chunk_size = 2000
    chunks = [context_text[i:i+chunk_size] for i in range(0, len(context_text), chunk_size)]
    
    group_id = str(uuid.uuid4())
    
    # Batch add to ChromaDB for speed
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_metas = [{
            "type": "FACT",
            "group_id": group_id,
            "chunk_index": i + j,
            "total_chunks": len(chunks),
            "entities": ""
        } for j in range(len(batch_chunks))]
        batch_ids = [str(uuid.uuid4()) for _ in batch_chunks]
        
        collection.add(
            documents=batch_chunks,
            metadatas=batch_metas,
            ids=batch_ids
        )
        
    # 3. Hijack memory_engine.py globals to use this temporary DB
    memory_engine._client = client
    memory_engine._collection = collection
    memory_engine.DB_PATH = db_path
    memory_engine.rolling_chat_buffer = []  # Clear history just in case
    
    return db_path, len(chunks)

def extract_choice(response):
    """Parse output to extract exactly A, B, C, or D following LongBench regex."""
    response = response.replace('*', '')
    match = re.search(r'The correct answer is \(([A-D])\)', response)
    if match: return match.group(1)
    
    match = re.search(r'The correct answer is ([A-D])', response)
    if match: return match.group(1)
    
    # Fallback to pure regex search if the strict sentence fails
    match = re.search(r'\b([A-D])\b', response)
    if match: return match.group(1)
    
    return None

def main():
    os.makedirs(DB_BASE_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    out_file = os.path.join(RESULTS_DIR, f"{memory_engine.LLM_MODEL.replace(':', '_')}_RAG.jsonl")
    
    # Load LongBench-v2 dataset
    print(f"Loading THUDM/LongBench-v2 dataset...")
    dataset = load_dataset('THUDM/LongBench-v2', split='train')
    
    # Cache to resume if interrupted
    has_data = set()
    if os.path.exists(out_file):
        with open(out_file, 'r', encoding='utf-8') as f:
            for line in f:
                has_data.add(json.loads(line)["_id"])
    
    fout = open(out_file, 'a', encoding='utf-8')
    
    for item in tqdm(dataset, desc="Evaluating"):
        item_id = item["_id"]
        if item_id in has_data:
            continue
            
        print(f"\n[{item_id}] Setting up isolated memory ({item['length']} length)...")
        start_embed = time.perf_counter()
        
        # 1. Create Isolated Memory DB
        db_path, num_chunks = create_isolated_memory(item_id, item['context'])
        print(f"[{item_id}] Embedded {num_chunks} chunks in {time.perf_counter()-start_embed:.1f}s")
        
        # 2. Construct Prompt
        # Force the engine to answer using the exact A/B/C/D format LongBench requires
        prompt = f"""Based on the provided context, please answer the question.
Your response MUST end with the EXACT phrase "The correct answer is (X)", where X is A, B, C, or D.

Question: {item['question']}

(A) {item['choice_A']}
(B) {item['choice_B']}
(C) {item['choice_C']}
(D) {item['choice_D']}
"""
        # 3. Execute Engine Search & Inference
        answer, timings = memory_engine.chat_logic(prompt)
        
        # 4. Extract Answer and Grade
        pred = extract_choice(answer)
        judge = pred == item["answer"]
        
        print(f"[{item_id}] RAG Engine Answer: {answer}")
        print(f"[{item_id}] Prediction: {pred} | Truth: {item['answer']} | Correct: {judge}")
        print(f"[{item_id}] Timings - Retrieval: {timings['retrieval']:.2f}s, Inference: {timings['inference']:.2f}s")
        
        # 5. Save Result
        result_item = {
            "_id": item_id,
            "domain": item["domain"],
            "sub_domain": item["sub_domain"],
            "difficulty": item["difficulty"],
            "length": item["length"],
            "question": item["question"],
            "choice_A": item["choice_A"],
            "choice_B": item["choice_B"],
            "choice_C": item["choice_C"],
            "choice_D": item["choice_D"],
            "answer": item["answer"],
            "pred": pred,
            "judge": judge,
            "response": answer,
            "context": item['context'][:1000]  # Just save the first 1000 chars of context
        }
        fout.write(json.dumps(result_item, ensure_ascii=False) + '\n')
        fout.flush()
        
        # 6. Cleanup (very important, or disk fills up fast with 503 DBs)
        memory_engine._client = None
        memory_engine._collection = None
        cleanup_db(db_path)
    
    print("\nEvaluation Complete.")
    print(f"Results saved to {out_file}")

if __name__ == "__main__":
    main()
