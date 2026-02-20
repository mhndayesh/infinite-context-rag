import os
import sys
import uuid
import threading
import warnings
import logging
import time
import json
import re
import time
import json

# --- PHASE VIII: SESSION-WINDOW VARIABLES ---
# Tracks the chronological context block for standard chat turns
current_session_block_id = str(uuid.uuid4())
last_interaction_time = time.time()
session_chunk_index = 0
IDLE_TIMEOUT_SECONDS = 300 # 5 Minutes of idle time generates a new block

# Silence all logging/warnings immediately
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)

import ollama
import chromadb
from chromadb.utils import embedding_functions

# Prevent local Ollama server from crashing under heavy async concurrent requests
inference_lock = threading.Lock()

# Import pynvml silently for VRAM check
try:
    import pynvml
except ImportError:
    pynvml = None

# --- CONFIGURATION ---
LLM_MODEL = "llama3.2:3b"
EMBED_MODEL = "nomic-embed-text"
DB_PATH = "./render_raw_memory_db"

_client = None
_collection = None

def get_collection():
    """Initializes ChromaDB with Ollama embeddings (Removing ONNX noise)."""
    global _client, _collection
    if _collection is None:
        # Use Ollama for embeddings so we don't need noisy C++ libraries
        emb_fn = embedding_functions.OllamaEmbeddingFunction(
            model_name=EMBED_MODEL,
            url="http://localhost:11434/api/embeddings",
        )
        
        _client = chromadb.PersistentClient(path=DB_PATH)
        _collection = _client.get_or_create_collection(
            name="raw_history",
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"} 
        )
    return _collection

# Rolling buffer for immediate conversation awareness (Max 3 turns)
rolling_chat_buffer = [] 

def check_vram():
    """Silently check VRAM and print only if critical."""
    if pynvml:
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            if (info.free / 1024**3) < 1.0:
                print(f"\n[!] ALERT: VRAM critically low ({info.free/1024**3:.2f}GB)")
        except:
            pass

def classify_memory(text):
    """JSON Chain-of-Thought Meta-Tagging: LLM strictly outputs structured schema."""
    prompt = f"""Analyze the provided text. You must output a strictly valid JSON object.
Step 1: Write a short 'justification' explaining if the text contains a concrete project FACT (password, strict configuration, name, specific instruction to memorize).
Step 2: If a fact exists, write it in 'extracted_entity'. If not, write 'none'.
Step 3: Output the final 'category' as exactly FACT or CHATTER.

JSON SCHEMA:
{{
  "justification": "string",
  "extracted_entity": "string",
  "category": "FACT|CHATTER"
}}

TEXT:
"{text}"
"""
    try:
        with inference_lock:
            # Force JSON structured output via Ollama API and ensure window
            response = ollama.chat(
                model=LLM_MODEL, 
                messages=[{'role': 'user', 'content': prompt}], 
                format='json',
                options={"num_ctx": 4096, "temperature": 0.1}
            )
        
        result_json = json.loads(response['message']['content'])
        ans = result_json.get('category', '').strip().upper()
        
        # Aggressive keyword fallback
        text_lower = text.lower()
        if "memorize" in text_lower or "exact answer" in text_lower or "secret" in text_lower:
            return "FACT"
            
        if "FACT" in ans: return "FACT"
        return "CHATTER"
    except Exception as e:
        print(f"\n[JSON Classifier Error] {e}")
        return "FACT" # Safest default

def extract_keywords(user_query):
    """
    PHASE IX: Agentic Query Expansion
    Uses the fast local model to rewrite a casual user query into dense keywords.
    """
    start_expand = time.perf_counter()
    try:
        from ollama import chat
        expansion_prompt = f"""You are a search query optimizer. 
Extract the core nouns, entities, themes, and specific details from the following user question.
Output ONLY a comma-separated list of keywords. Do NOT write sentences. Do NOT answer the question.

USER QUESTION: "{user_query}"
KEYWORDS:"""
        
        with inference_lock:
            response = chat(
                model=LLM_MODEL,
                messages=[{'role': 'system', 'content': 'You extract keywords only. No formatting. No sentences.'},
                          {'role': 'user', 'content': expansion_prompt}],
                options={"num_ctx": 4096, "temperature": 0.0}
            )
        keywords = response['message']['content'].strip()
        print(f"\n   [Pre-Search Expander] Rewrote '{user_query}' -> '{keywords}'")
        return keywords
    except Exception as e:
        print(f"\n   [Pre-Search Error] Falling back to raw query. {e}")
        return user_query

def chat_logic(user_input):
    global rolling_chat_buffer, current_session_block_id, last_interaction_time, session_chunk_index
    collection = get_collection()
    
    # --- PHASE VIII: SESSION IDLE CHECK ---
    # If the user has been idle for 5 minutes, generate a new narrative "block" ID
    current_time = time.time()
    if (current_time - last_interaction_time) > IDLE_TIMEOUT_SECONDS:
        current_session_block_id = str(uuid.uuid4())
        session_chunk_index = 0
        print(f"\n[Session Manager] Idle timeout detected (>5m). Began new session block: {current_session_block_id[:8]}...")
    last_interaction_time = current_time

    # --- DYNAMIC INPUT CHUNKING (Power User Protection) ---
    # If the user pastes a massive block, we embed it immediately in pieces before answering
    if len(user_input) > 2000:
        def _pre_embed_chunks(text):
            chunk_size = 2000
            local_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            # Generate a unique ID for this entire document/paste
            group_id = str(uuid.uuid4())
            
            for idx, chunk in enumerate(local_chunks):
                try:
                    collection.add(
                        documents=[chunk],
                        metadatas=[{
                            "type": "FACT",
                            "group_id": group_id,
                            "chunk_index": idx,
                            "total_chunks": len(local_chunks)
                        }], # Treat large pastes as factual project data with group association
                        ids=[str(uuid.uuid4())]
                    )
                except Exception as e:
                    print(f"\n[Chunk Embed Error] {e}")
        # Run this in background to avoid blocking the first response too long
        threading.Thread(target=_pre_embed_chunks, args=(user_input,), daemon=True).start()

    # Use max 2000 chars for the embedding query limitation check
    safe_query_input = user_input[:2000]

    # --- PHASE IX: Agentic Query Expansion ---
    expanded_query = extract_keywords(safe_query_input)

    # 1. Fetch memory (Stage 1: Broad Search for Top 10 Hits)
    start_retrieve = time.perf_counter()
    try:
        # We query the DB using the dense, optimized keywords, not the casual human sentence
        results = collection.query(query_texts=[expanded_query], n_results=10)
        doc_hits = results['documents'][0] if results and results['documents'] else []
        meta_hits = results['metadatas'][0] if results and results['metadatas'] else []
        print(f"   [RAG Stage 1] Found {len(doc_hits)} vector hits.")
    except:
        doc_hits = []
        meta_hits = []

    # Stage 2: Agentic Selection (Which chunk actually matters?)
    target_group_id = None
    if len(doc_hits) > 1:
        snippet_list = ""
        # Evaluate up to the top 3 hits in FULL to fit within router 4k window
        eval_hits = doc_hits[:3] 
        for i, doc in enumerate(eval_hits):
            snippet_list += f"\n--- SNIPPET {i} ---\n{doc}\n" 
            
        selection_prompt = f"""You are a search router. The user asked: "{user_input}"
Below are {len(eval_hits)} snippets from a database. 
Identify WHICH SINGLE SNIPPET is MOST LIKELY to contain the answer or be relevant to the topic. 
Output ONLY the integer number of the snippet (e.g., 0, 1, 2). If absolutely none seem relevant, output 0 as a default. Do not explain.

{snippet_list}
"""
        try:
            with inference_lock:
                sel_response = ollama.chat(
                    model=LLM_MODEL, 
                    messages=[{'role': 'system', 'content': 'You are a strict routing AI. Only output integers.'},
                              {'role': 'user', 'content': selection_prompt}],
                    options={"num_ctx": 4096, "temperature": 0.0} # Zero temp for strict logic
                )
            sel_ans = sel_response['message']['content'].strip()
            # Extract the first integer found
            match = re.search(r'-?\d+', sel_ans)
            print(f"   [Agentic Route] LLM raw output: '{sel_ans}'")
            if match:
                selected_idx = int(match.group())
                print(f"   [Agentic Route] Extracted index: {selected_idx} (out of {len(eval_hits)})")
                if 0 <= selected_idx < len(eval_hits):
                    target_group_id = meta_hits[selected_idx].get("group_id")
        except Exception as e:
            print(f"\n[Agentic Selection Error] {e}")

    # Fallback to the top 1 if selection fails
    if target_group_id is None and len(meta_hits) > 0:
        if isinstance(meta_hits[0], dict) and "group_id" in meta_hits[0]:
            target_group_id = meta_hits[0]["group_id"]
            print(f"   [Agentic Route] Fallback to top hit group: {target_group_id}")
        else:
             print("   [Agentic Route] Fallback failed: Top hit has no group_id")


    # Stage 3: Full Context Exhumation (Dynamically Centered)
    facts = []
    if target_group_id:
        try:
            # Fetch ALL chunks sharing this group_id
            group_results = collection.get(where={"group_id": target_group_id})
            group_docs = group_results['documents']
            group_metas = group_results['metadatas']
            
            # Sort them back into original order
            combined = list(zip(group_docs, group_metas))
            combined.sort(key=lambda x: x[1].get("chunk_index", 0))
            
            # Find the center index (the snippet the AI routed us to)
            target_chunk_idx = meta_hits[selected_idx].get("chunk_index", 0) if 'selected_idx' in locals() and 0 <= selected_idx < len(meta_hits) else 0
            
            center_idx = 0
            for k, (_, meta) in enumerate(combined):
                if meta.get("chunk_index", -1) == target_chunk_idx:
                    center_idx = k
                    break
                    
            # Expand outwards from the center chunk until we hit our ~8000 char budget
            budget = 8000
            current_len = len(combined[center_idx][0])
            included_indices = [center_idx]
            
            left, right = center_idx - 1, center_idx + 1
            while (left >= 0 or right < len(combined)) and current_len < budget:
                # Prioritize content *before* the hit to provide leading context, then after
                if left >= 0:
                    l_len = len(combined[left][0])
                    if current_len + l_len <= budget:
                        included_indices.append(left)
                        current_len += l_len
                    left -= 1
                if right < len(combined) and current_len < budget:
                    r_len = len(combined[right][0])
                    if current_len + r_len <= budget:
                        included_indices.append(right)
                        current_len += r_len
                    right += 1
                    
            included_indices.sort()
            for k in included_indices:
                facts.append(combined[k][0])
                
            print(f"   [RAG Stage 3] Reassembled contextual window ({current_len} chars) around chunk {center_idx} (Group: {target_group_id[:8]}...)")
        except Exception as e:
            print(f"\n[Group Retrieval Error] {e}")
            facts = doc_hits[:3] # Fallback to standard top 3 hits
    else:
        facts = doc_hits[:3] # Use standard hits if no groupped data is found
    end_retrieve = time.perf_counter()
    retrieve_time = end_retrieve - start_retrieve
        
    # --- PRACTICAL POWER USER GUARD (4k Token Balance) ---
    
    # 1. Retrieved Context: 8000 chars (~2k tokens) - Prioritize the retrieved "Whole Document/Session Block"
    combined_memory = facts
    past_memory = "\n---\n".join(combined_memory)[:8000] 

    # 2. Build prompt with strict budgeting
    system_prompt = f"""You are a highly capable AI Memory Engine. 
Your Absolute Priority is to answer the user's question using the following Historical Facts/Memory Database.
If the answer exists in the data below, you MUST provide it exactly as written. Do not refuse to answer if the context is available.

HISTORICAL DATABASE:
{past_memory}
---"""
    
    # 3. User Input Guard: 2000 chars max (Leave room for 12k char Memory + Buffer)
    safe_input = user_input[:2000]
    
    messages = [{'role': 'system', 'content': system_prompt}]
    
    # 4. Chat History Guard: 2000 chars max (Condensed context)
    buffer_text = ""
    safe_buffer = []
    for msg in reversed(rolling_chat_buffer):
        if len(buffer_text) + len(msg['content']) < 2000:
            safe_buffer.insert(0, msg)
            buffer_text += msg['content']
        else:
            break
            
    messages.extend(safe_buffer)
    messages.append({'role': 'user', 'content': safe_input})

    # 3. LLM Answer (Strict 4k Window context for Full-Document RAG)
    start_inference = time.perf_counter()
    with inference_lock:
        response = ollama.chat(
            model=LLM_MODEL, 
            messages=messages,
            options={"num_ctx": 4096, "temperature": 0.2}
        )
    ai_answer = response['message']['content']
    end_inference = time.perf_counter()
    inference_time = end_inference - start_inference
    
    # --- PREFIX SANITIZATION ---
    # Strip common AI-generated prefixes to prevent contextual recursion (AI: AI: ...)
    clean_answer = ai_answer
    for prefix in ["AI:", "Assistant:", "Assistant Reply:", "Answer:"]:
        if clean_answer.lstrip().startswith(prefix):
            clean_answer = clean_answer.lstrip()[len(prefix):].strip()
            break
    
    # 4. Async Save (with Meta-Tagging & Session Chunking)
    def _save():
        global session_chunk_index
        start_save = time.perf_counter()
        try:
            combined_text = f"U: {safe_input}\nAI: {clean_answer}"
            memory_type = classify_memory(combined_text)
            
            # --- PHASE VIII: SESSION GROUPING ---
            metadata = {
                "type": memory_type,
                "group_id": current_session_block_id,
                "chunk_index": session_chunk_index
            }
            session_chunk_index += 1
            
            collection.add(
                documents=[combined_text],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())]
            )
            end_save = time.perf_counter()
            # Still print for real-time monitoring
            print(f"   [PERF] Retrieval: {retrieve_time:.3f}s | Inference: {inference_time:.3f}s | Save/Embed: {end_save - start_save:.3f}s")
        except Exception as e:
            print(f"\n[Save Error] {e}")
            
    threading.Thread(target=_save, daemon=True).start()

    # 5. Buffer Update
    rolling_chat_buffer.append({'role': 'user', 'content': safe_input})
    rolling_chat_buffer.append({'role': 'assistant', 'content': clean_answer})
    if len(rolling_chat_buffer) > 6:
        rolling_chat_buffer = rolling_chat_buffer[-6:]

    timings = {
        "retrieval": retrieve_time,
        "inference": inference_time
    }
    return clean_answer, timings

if __name__ == "__main__":
    print("="*40)
    print("SESSION MEMORY ENGINE ACTIVE")
    print(" (Now running noise-free via Ollama) ")
    print("="*40)
    
    try:
        while True:
            check_vram()
            user_in = input("\nYou: ")
            if user_in.lower() in ['exit', 'quit']: break
            if not user_in.strip(): continue
            
            print("\nAI: ", end="", flush=True)
            answer, _ = chat_logic(user_in)
            print(answer)
    except KeyboardInterrupt:
        pass
    print("\nSession saved. Goodbye.")
