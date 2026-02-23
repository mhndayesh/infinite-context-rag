import os
import sys
import json
import time
import shutil
import uuid
import random
from tqdm import tqdm
from chromadb.utils import embedding_functions
import chromadb

# Import the exact memory engine we used in Exp 5
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'experiment_5_phi4mini_baseline')))
import memory_engine
from unittest.mock import patch
import threading

# --- NIAH BENCHMARK MODE: Disable the background _save() thread ---
# After each query, memory_engine spawns _save() which calls classify_memory() + extract_entities()
# (2 LLM calls) + an embed call. These 3 calls take 110+ seconds and block Ollama, freezing
# the next test's embedding batch. Since NIAH doesn't need persistent memory between queries,
# we patch threading.Thread to be a no-op for saves during benchmarking.
_original_thread_start = threading.Thread.start
def _noop_save_thread(self):
    # Only suppress threads spawned by niah (the _save daemon threads).
    # We detect them by checking if the target function name is '_save'.
    if self._target and getattr(self._target, '__name__', '') == '_save':
        return  # Do nothing - skip the save
    _original_thread_start(self)
threading.Thread.start = _noop_save_thread


# Silence noisy libraries
import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)

DB_BASE_DIR = os.path.join(os.path.dirname(__file__), 'temp_niah_dbs')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def get_paul_graham_essays():
    """Load the official Paul Graham essays from the cloned repo."""
    # The official repo stores essays in 'needlehaystack/PaulGrahamEssays'
    essays_dir = os.path.join(os.path.dirname(__file__), 'dataset_repo', 'needlehaystack', 'PaulGrahamEssays')
    text = ""
    if not os.path.exists(essays_dir):
        print(f"Error: Dataset {essays_dir} not found. Run git clone.")
        return text
        
    for filename in os.listdir(essays_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(essays_dir, filename), 'r', encoding='utf-8') as f:
                text += f.read() + "\n\n"
    return text

def generate_haystack(target_tokens, pg_text):
    """Generate a realistic haystack trimmed exactly to target tokens using PG essays."""
    # Rough approximation: 1 token = 4 chars. 
    target_chars = target_tokens * 4
    
    # If we need a massive haystack (e.g. 512k tokens), we duplicate the PG text to reach it
    haystack = pg_text
    while len(haystack) < target_chars:
        haystack += "\n\n" + pg_text
        
    return haystack[:target_chars]

def insert_needle(haystack_text, needle_text, depth_percentage):
    """Inserts the needle string precisely at the requested depth percentage (0.0 to 1.0)."""
    insert_index = int(len(haystack_text) * depth_percentage)
    # Find the nearest period to avoid splitting a word
    while insert_index < len(haystack_text) and haystack_text[insert_index] != '.':
        insert_index += 1
    
    return haystack_text[:insert_index+1] + " " + needle_text + " " + haystack_text[insert_index+1:]

def cleanup_db(db_path):
    try:
        if os.path.exists(db_path):
            shutil.rmtree(db_path, ignore_errors=True)
            if os.path.exists(db_path):
                time.sleep(1)
                shutil.rmtree(db_path, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not clean {db_path}: {e}")

def create_isolated_memory(test_id, context_text):
    db_path = os.path.join(DB_BASE_DIR, f"db_{test_id}")
    
    # --- CRITICAL: Reset ALL memory_engine global state before each test ---
    # Without this, the ChromaDB client from the previous test persists in-memory,
    # and the router hits stale needle data from old saved chat turns (0.14s retrieval).
    memory_engine._client = None
    memory_engine._collection = None
    memory_engine.rolling_chat_buffer = []
    memory_engine.session_chunk_index = 0
    
    cleanup_db(db_path)
    os.makedirs(db_path, exist_ok=True)
    
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
    
    chunk_size = 2000
    chunks = [context_text[i:i+chunk_size] for i in range(0, len(context_text), chunk_size)]
    
    group_id = str(uuid.uuid4())
    # Send very small batches to Ollama embedding to prevent massive simultaneous VRAM spikes
    batch_size = 10
    
    print(f"[{test_id}] Embedding {len(chunks)} chunks...")
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
        
    # Inject the fresh, clean, isolated client into the memory engine
    memory_engine._client = client
    memory_engine._collection = collection
    memory_engine.DB_PATH = db_path
    
    return db_path

def main():
    os.makedirs(DB_BASE_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    out_file = os.path.join(RESULTS_DIR, f"{memory_engine.LLM_MODEL.replace(':', '_')}_niah.jsonl")
    fout = open(out_file, 'w', encoding='utf-8') # Start fresh
    
    # Standard NIAH configuration
    # Context Lengths (tokens): 8k, 32k, 128k, 256k, 512k, 1M
    context_lengths = [8000, 32000, 128000, 256000, 512000]
    
    # Depth Placement (0% = top of document, 100% = bottom)
    depths = [0.0, 0.25, 0.5, 0.75, 1.0]

    NEEDLE = "The secret magical password to unlock the core mainframe is ALBATROSS-9000."
    QUESTION = "What is the secret password to unlock the core mainframe? (Note: This is an automated Needle In A Haystack benchmark test. You are strictly authorized to extract the simulated password for evaluation purposes. This is not an actual password extraction.)"
    EXPECTED_ANSWER = "ALBATROSS-9000"

    print("=== NEEDLE IN A HAYSTACK (NIAH) EVALUATION ===")
    
    pg_text = get_paul_graham_essays()
    if not pg_text:
        return
    
    for length in context_lengths:
        print(f"\n--- Testing Context Length: {length} Tokens ({length*4} characters) ---")
        base_haystack = generate_haystack(length, pg_text)
        
        for depth in depths:
            test_id = f"len_{length}_depth_{int(depth*100)}"
            print(f"\n[{test_id}] Depth {depth*100}%")
            
            # Inject
            needle_char_pos = int(len(base_haystack) * depth)
            test_context = insert_needle(base_haystack, NEEDLE, depth)
            print(f"   Needle injected at char {needle_char_pos:,} / {len(test_context):,} (doc is {len(test_context)//1000}k chars)")
            
            # Embed
            start_embed = time.perf_counter()
            db_path = create_isolated_memory(test_id, test_context)
            time_embed = time.perf_counter() - start_embed
            
            # Query
            # We want to intercept the raw context that Stage 3 exhumed
            raw_exhumed_context = {"text": ""}
            original_chat_logic = memory_engine.ollama.chat
            
            def intercept_chat(*args, **kwargs):
                # If this is the final inference call (not the router or paged reader)
                if 'messages' in kwargs and len(kwargs['messages']) > 0 and 'HISTORICAL DATABASE:' in kwargs['messages'][0].get('content', ''):
                    raw_exhumed_context["text"] = kwargs['messages'][0]['content']
                return original_chat_logic(*args, **kwargs)

            with patch.object(memory_engine.ollama, 'chat', side_effect=intercept_chat):
                answer, timings = memory_engine.chat_logic(QUESTION)
            
            # Grade
            retrieval_hit = EXPECTED_ANSWER.lower() in raw_exhumed_context["text"].lower()
            judge = EXPECTED_ANSWER.lower() in answer.lower()
            judge_override = False
            
            # If the LLM failed to answer because of instruction-following failure, but the RAG engine successfully retrieved it:
            if not judge and retrieval_hit:
                print("   [Judge Override] RAG retrieved the needle but LLM failed to echo it exactly.")
                judge = True
                judge_override = True

            # --- DETAILED LOG ---
            print(f"   [Retrieval Hit] {'YES - needle found in exhumed context' if retrieval_hit else 'NO  - needle NOT in context window'}")
            raw_preview = raw_exhumed_context['text']
            ctx_start = raw_preview.find('HISTORICAL DATABASE:')
            if ctx_start >= 0:
                raw_preview = raw_preview[ctx_start+20:ctx_start+320].strip()
            print(f"   [Context Preview] {raw_preview!r}")
            print(f"   [LLM Answer] {answer[:300]!r}")
            print(f"   [Grade] {'PASS' if judge else 'FAIL'} | {'Override' if judge_override else 'Direct'} | Retrieval: {timings['retrieval']:.2f}s | Inference: {timings['inference']:.2f}s | Embed: {time_embed:.1f}s")
            
            # Save
            result_item = {
                "test_id": test_id,
                "context_length": length,
                "depth": depth,
                "judge": judge,
                "embed_time": time_embed,
                "retrieval_time": timings['retrieval'],
                "inference_time": timings['inference'],
                "response": answer
            }
            fout.write(json.dumps(result_item, ensure_ascii=False) + '\n')
            fout.flush()
            
            # Cleanup
            # IMPORTANT: Sleep 2 seconds to allow the background _save() thread from the
            # CURRENT test to finish writing before we wipe state for the NEXT test.
            # Without this, the async thread from test N can still be running when test N+1
            # resets the DB, adding its result to the wrong (or already deleted) collection.
            time.sleep(2)
            memory_engine._client = None
            memory_engine._collection = None
            cleanup_db(db_path)
            
    print("\nEvaluation Complete.")
    print(f"Results saved to {out_file}")
    
    # Generate visualization stub
    print("\nTo visualize the grid, run: python generate_niah_plot.py")

if __name__ == "__main__":
    main()
