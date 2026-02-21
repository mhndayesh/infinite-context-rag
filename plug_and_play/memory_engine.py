"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           AGENTIC RAG MEMORY ENGINE  —  Plug & Play Edition               ║
║           github.com/mhndayesh/infinite-context-rag                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Best result: phi4-mini:3.8b + Baseline RAG = 5/5 at 512k token depth     ║
║  Runs 100% locally · No cloud APIs · $0 per query · Full data privacy      ║
╚══════════════════════════════════════════════════════════════════════════════╝

QUICK START
-----------
  1. Install Ollama  →  https://ollama.com
  2. pip install chromadb ollama pynvml
  3. ollama pull phi4-mini:3.8b
  4. ollama pull nomic-embed-text
  5. python memory_engine.py          ← interactive chat
     -- OR --
  5. from memory_engine import chat_logic   ← import into your project

HOW IT WORKS (at a glance)
---------------------------
  When you send a message:
    1. The LLM rewrites your question into dense search keywords
    2. ChromaDB finds the top 10 closest chunks in memory
    3. Another LLM call picks the best match
    4. We retrieve the ENTIRE conversation block around that match
    5. Entity cheat sheets (names, numbers, dates) are prepended for recall
    6. If context is big, pages are read independently to prevent 'lost in middle'
    7. Final LLM answer is generated inside a 4,096-token context window
    8. The conversation is saved to ChromaDB asynchronously in the background
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: STANDARD LIBRARY IMPORTS  (no changes needed here)
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import uuid
import threading
import warnings
import logging
import time
import json
import re

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: ⚙️  CONFIGURATION  — CHANGE THESE TO FIT YOUR SETUP
# ─────────────────────────────────────────────────────────────────────────────

# ┌─ CONFIGURATION (Environment variables override these defaults) ───────────┐
# │                                                                            │
# │  OLLAMA_URL  — URL of your Ollama server.                                  │
# │  LLM_MODEL   — Main reasoning model (e.g., phi4-mini:3.8b)                │
# │  EMBED_MODEL — Embedding model for search (e.g., nomic-embed-text)         │
# │  DB_PATH     — File path for the persistent memory database                │
# │  NUM_CTX     — LLM context window size (e.g., 4096)                       │
# │  IDLE_TIMEOUT_SECONDS — Seconds before starting a new chat session block    │
# │                                                                            │
# └────────────────────────────────────────────────────────────────────────────┘
OLLAMA_URL           = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL            = os.getenv("LLM_MODEL", "phi4-mini:3.8b")
EMBED_MODEL          = os.getenv("EMBED_MODEL", "nomic-embed-text")
DB_PATH              = os.getenv("DB_PATH", "./memory_db")
NUM_CTX              = int(os.getenv("NUM_CTX", "4096"))
IDLE_TIMEOUT_SECONDS = int(os.getenv("IDLE_TIMEOUT_SECONDS", "300"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: INITIALIZATION  (no changes needed)
# ─────────────────────────────────────────────────────────────────────────────

# Silence chromadb and ONNX runtime noise
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)

import ollama
import chromadb
from chromadb.utils import embedding_functions

# Serializes LLM calls to prevent Ollama server crashes under concurrent load.
# Ollama's local server can't handle two simultaneous requests safely.
inference_lock = threading.Lock()

# Optional: VRAM monitoring (install with: pip install pynvml)
try:
    import pynvml
except ImportError:
    pynvml = None

# Session tracking — these are managed automatically, no need to touch them
current_session_block_id = str(uuid.uuid4())
last_interaction_time = time.time()
session_chunk_index = 0
rolling_chat_buffer = []

# Lazy ChromaDB client (initialized on first use)
_client = None
_collection = None


def get_collection():
    """
    Initializes the ChromaDB vector database with Ollama embeddings.
    Called automatically on first use. The DB folder is created if needed.
    """
    global _client, _collection
    if _collection is None:
        emb_fn = embedding_functions.OllamaEmbeddingFunction(
            model_name=EMBED_MODEL,
            url=f"{OLLAMA_URL}/api/embeddings",
        )
        _client = chromadb.PersistentClient(path=DB_PATH)
        _collection = _client.get_or_create_collection(
            name="memory",
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: INTERNAL PIPELINE FUNCTIONS  (no changes needed)
# ─────────────────────────────────────────────────────────────────────────────

def check_vram():
    """Silently warns if VRAM is critically low (< 1GB free)."""
    if pynvml:
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            if (info.free / 1024**3) < 1.0:
                print(f"\n[!] VRAM Warning: Only {info.free/1024**3:.2f}GB free.")
        except:
            pass


def classify_memory(text):
    """
    STAGE 0A: Memory Classifier
    Decides if a conversation turn contains anything worth remembering (FACT)
    or is just small talk (CHATTER). Only FACTs trigger entity extraction.
    """
    prompt = f"""Analyze the provided text. Output valid JSON only.
Step 1: Write a short 'justification' — does this text contain a proper name, number, date, budget, location, technical ID, or any instruction to memorize?
Step 2: If ANY specific data exists, write it in 'extracted_entity'. Otherwise write 'none'.
Step 3: Output 'category' as exactly FACT or CHATTER. Default to FACT if uncertain.

JSON SCHEMA:
{{
  "justification": "string",
  "extracted_entity": "string",
  "category": "FACT|CHATTER"
}}

TEXT:
"{text[:1500]}"
"""
    try:
        with inference_lock:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                format='json',
                options={"num_ctx": NUM_CTX, "temperature": 0.1}
            )
        result_json = json.loads(response['message']['content'])
        ans = result_json.get('category', '').strip().upper()

        # Keyword override: if user explicitly asks to memorize, always FACT
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["memorize", "remember this", "commit to memory", "secret"]):
            return "FACT"

        return "FACT" if "FACT" in ans else "CHATTER"
    except Exception as e:
        return "FACT"  # Safe default — better to over-store than lose data


def extract_entities(text):
    """
    STAGE 0B: Entity Extraction (Phase XI-A)
    Extracts names, numbers, dates, and technical IDs from a conversation turn.
    These are stored in ChromaDB metadata and prepended as 'cheat sheets'
    at query time to prevent critical facts from being lost in the context window.
    """
    try:
        with inference_lock:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': 'You extract entities only. Output a comma-separated list. No sentences. No duplicates.'},
                    {'role': 'user', 'content': f"""Extract ALL proper nouns, specific numbers, dates, percentages, dollar amounts, technical terms, and unique names.
Output ONLY a comma-separated list. Do NOT write sentences.

TEXT: "{text[:2000]}"
ENTITIES:"""}
                ],
                options={"num_ctx": NUM_CTX, "temperature": 0.0}
            )
        entities = response['message']['content'].strip()
        # Deduplicate to prevent repetition loops
        unique = list(dict.fromkeys([e.strip() for e in entities.split(',') if e.strip()]))
        return ', '.join(unique)[:300]  # Cap to prevent metadata bloat
    except:
        return ""


def extract_keywords(user_query):
    """
    STAGE 1A: Agentic Query Expansion (Phase IX)
    Rewrites the user's casual question into dense search keywords.
    This dramatically improves vector search accuracy — searching
    "Leviathan, submersible, October 4th, budget" finds the right chunk
    far better than searching "what was the name of that submarine again?"
    """
    try:
        with inference_lock:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': 'You extract keywords only. No formatting. No sentences.'},
                    {'role': 'user', 'content': f"""Extract the core nouns, entities, themes, and specific details from this question.
Output ONLY a comma-separated list of keywords. Do NOT answer the question.

QUESTION: "{user_query}"
KEYWORDS:"""}
                ],
                options={"num_ctx": NUM_CTX, "temperature": 0.0}
            )
        keywords = response['message']['content'].strip()
        unique_kws = list(dict.fromkeys([k.strip() for k in keywords.split(',') if k.strip()]))
        result = ', '.join(unique_kws)[:500]  # Hard cap at 500 chars (embedding limit)
        print(f"\n   [Expander] '{user_query[:60]}' -> '{result[:60]}'")
        return result
    except Exception as e:
        return user_query[:500]  # Fallback to raw query


def paged_context_read(pages, user_query):
    """
    STAGE 3B: Paged Context Reading (Phase XI-B)
    When a retrieved session block is large (> 4,000 chars), it is split
    into pages. The LLM reads each page independently and extracts only
    the relevant facts. This prevents 'Lost in the Middle' failure mode
    where the LLM ignores content buried in the middle of a long context.
    """
    findings = []
    for page_num, page_text in enumerate(pages):
        try:
            with inference_lock:
                response = ollama.chat(
                    model=LLM_MODEL,
                    messages=[
                        {'role': 'system', 'content': 'You are a fact extractor. Extract ONLY facts relevant to the question. Output a concise bulleted list. If nothing is relevant, output "NOTHING RELEVANT".'},
                        {'role': 'user', 'content': f"""QUESTION: "{user_query[:500]}"

--- PAGE {page_num + 1} ---
{page_text}
--- END PAGE ---

Relevant facts:"""}
                    ],
                    options={"num_ctx": NUM_CTX, "temperature": 0.0}
                )
            page_findings = response['message']['content'].strip()
            if "NOTHING RELEVANT" not in page_findings.upper():
                findings.append(page_findings)
                print(f"   [Paged Reader] Page {page_num + 1}: Found relevant facts.")
            else:
                print(f"   [Paged Reader] Page {page_num + 1}: Nothing relevant.")
        except Exception as e:
            print(f"   [Paged Reader Error] Page {page_num + 1}: {e}")

    return "\n".join(findings) if findings else ""


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: MAIN CHAT FUNCTION  — this is what you call from your code
# ─────────────────────────────────────────────────────────────────────────────

def chat_logic(user_input: str) -> tuple[str, dict]:
    """
    ╔══════════════════════════════════════════════════════════════╗
    ║  MAIN ENTRY POINT — Call this from your app or agent        ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Args:                                                       ║
    ║    user_input (str) — the user's message                    ║
    ║                                                              ║
    ║  Returns:                                                    ║
    ║    (str, dict) — (AI answer, {retrieval_s, inference_s})    ║
    ╚══════════════════════════════════════════════════════════════╝

    Integration examples:
    ─────────────────────
    # Simplest use:
    answer, _ = chat_logic("What was the budget for Project Vanguard?")
    print(answer)

    # With timings:
    answer, timings = chat_logic("Summarize our Q3 marketing metrics")
    print(f"Answer: {answer}")
    print(f"Retrieved in {timings['retrieval']:.2f}s, answered in {timings['inference']:.2f}s")

    # In an agent loop:
    while True:
        user_msg = get_user_message()   # your function
        reply, _ = chat_logic(user_msg)
        send_to_user(reply)             # your function
    """
    global rolling_chat_buffer, current_session_block_id, last_interaction_time, session_chunk_index
    collection = get_collection()

    # ── SESSION BLOCK MANAGEMENT ───────────────────────────────────────────
    # Groups messages into conversation blocks. After IDLE_TIMEOUT_SECONDS of
    # silence, a new block starts. This keeps unrelated conversations separated
    # in the database for cleaner retrieval.
    current_time = time.time()
    if (current_time - last_interaction_time) > IDLE_TIMEOUT_SECONDS:
        current_session_block_id = str(uuid.uuid4())
        session_chunk_index = 0
        print(f"\n[Session] New block started: {current_session_block_id[:8]}...")
    last_interaction_time = current_time

    # ── LARGE INPUT CHUNKING ───────────────────────────────────────────────
    # If a user pastes a large document (> 3000 chars), pre-embed it in chunks
    # in the background. This ensures large pastes are searchable immediately.
    if len(user_input) > 3000:
        def _pre_embed_chunks(text):
            chunk_size = 2000
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            group_id = str(uuid.uuid4())
            for idx, chunk in enumerate(chunks):
                try:
                    collection.add(
                        documents=[chunk],
                        metadatas=[{"type": "FACT", "group_id": group_id,
                                    "chunk_index": idx, "total_chunks": len(chunks), "entities": ""}],
                        ids=[str(uuid.uuid4())]
                    )
                except Exception as e:
                    print(f"\n[Chunk Embed Error] {e}")
        threading.Thread(target=_pre_embed_chunks, args=(user_input,), daemon=True).start()

    # ── STAGE 1: QUERY EXPANSION + VECTOR SEARCH ──────────────────────────
    expanded_query = extract_keywords(user_input[:2000])

    start_retrieve = time.perf_counter()
    try:
        results = collection.query(query_texts=[expanded_query[:500]], n_results=10)
        doc_hits = results['documents'][0] if results and results['documents'] else []
        meta_hits = results['metadatas'][0] if results and results['metadatas'] else []
        print(f"   [RAG Stage 1] Found {len(doc_hits)} vector hits.")
    except:
        doc_hits, meta_hits = [], []

    # ── STAGE 2: AGENTIC ROUTING ───────────────────────────────────────────
    # The LLM picks which of the top 3 results is actually relevant to the query.
    # This prevents the wrong session from being exhumed.
    target_group_id = None
    selected_idx = 0  # Default to top result
    if len(doc_hits) > 1:
        snippet_list = ""
        eval_hits = doc_hits[:3]
        for i, doc in enumerate(eval_hits):
            snippet_list += f"\n--- SNIPPET {i} ---\n{doc[:800]}\n"

        selection_prompt = f"""You are a search router. User asked: "{user_input[:200]}"
Which SINGLE snippet is most likely to contain the answer?
Output ONLY the integer index (0, 1, or 2). Nothing else.

{snippet_list}
"""
        try:
            with inference_lock:
                sel_response = ollama.chat(
                    model=LLM_MODEL,
                    messages=[
                        {'role': 'system', 'content': 'Output only an integer.'},
                        {'role': 'user', 'content': selection_prompt}
                    ],
                    options={"num_ctx": NUM_CTX, "temperature": 0.0}
                )
            match = re.search(r'\d+', sel_response['message']['content'].strip())
            if match:
                selected_idx = min(int(match.group()), len(eval_hits) - 1)
                target_group_id = meta_hits[selected_idx].get("group_id")
                print(f"   [Agentic Route] Selected snippet {selected_idx}")
        except Exception as e:
            print(f"\n[Routing Error] {e}")

    # Fallback: use the top hit
    if target_group_id is None and meta_hits:
        target_group_id = meta_hits[0].get("group_id")

    # ── STAGE 3: GROUP EXHUMATION ──────────────────────────────────────────
    # Fetch ALL chunks from the same conversation block, then reassemble them
    # in order around the matched chunk. This gives the LLM a clean, complete,
    # chronological view of the relevant conversation — not just a single snippet.
    facts = []
    cheat_sheet_entities = []
    if target_group_id:
        try:
            group_results = collection.get(where={"group_id": target_group_id})
            combined = sorted(
                zip(group_results['documents'], group_results['metadatas']),
                key=lambda x: x[1].get("chunk_index", 0)
            )

            # Find the center chunk (the one the router picked)
            target_chunk_idx = meta_hits[selected_idx].get("chunk_index", 0) if selected_idx < len(meta_hits) else 0
            center_idx = next((k for k, (_, m) in enumerate(combined)
                               if m.get("chunk_index") == target_chunk_idx), 0)

            # Expand outward from center until we hit the 6,000-char budget
            budget = 6000
            current_len = len(combined[center_idx][0])
            included = [center_idx]
            left, right = center_idx - 1, center_idx + 1
            while (left >= 0 or right < len(combined)) and current_len < budget:
                if left >= 0 and current_len + len(combined[left][0]) <= budget:
                    included.append(left)
                    current_len += len(combined[left][0])
                    left -= 1
                elif left >= 0:
                    left -= 1
                if right < len(combined) and current_len + len(combined[right][0]) <= budget:
                    included.append(right)
                    current_len += len(combined[right][0])
                    right += 1
                elif right < len(combined):
                    right += 1

            included.sort()
            for k in included:
                facts.append(combined[k][0])
                ent = combined[k][1].get("entities", "")
                if ent:
                    cheat_sheet_entities.append(ent)

            print(f"   [RAG Stage 3] Assembled {current_len} chars around chunk {center_idx} (Group: {target_group_id[:8]}...)")

            # ── PHASE XI-B: Paged Context Reading ─────────────────────────
            raw_context = "\n---\n".join(facts)
            pages = [raw_context[i:i+4000] for i in range(0, len(raw_context), 4000)]
            if len(pages) > 1:
                print(f"   [Paged Reader] {len(raw_context)} chars → {len(pages)} pages")
                condensed = paged_context_read(pages, user_input[:500])
                if condensed:
                    facts = [condensed]

            # ── PHASE XI-A: Entity Cheat Sheet ────────────────────────────
            if cheat_sheet_entities:
                cheat_text = "KEY ENTITIES: " + ", ".join(cheat_sheet_entities)
                facts.insert(0, cheat_text)
                print(f"   [Cheat Sheet] Pinned {len(cheat_text)} chars of key entities.")

        except Exception as e:
            print(f"\n[Group Retrieval Error] {e}")
            facts = doc_hits[:3]
    else:
        facts = doc_hits[:3]

    end_retrieve = time.perf_counter()
    retrieve_time = end_retrieve - start_retrieve

    # ── FINAL ANSWER GENERATION ────────────────────────────────────────────
    # Pack retrieved context into the system prompt (6,000 char cap = ~1,500 tokens)
    # leaving ~2,500 tokens for the user message, chat buffer, and output.
    past_memory = "\n---\n".join(facts)[:6000]

    system_prompt = f"""You are a highly capable AI Memory Engine.
Your absolute priority is to answer the user's question using the HISTORICAL DATABASE below.
If the answer exists in the data, you MUST provide it exactly as written. Do not refuse.

HISTORICAL DATABASE:
{past_memory}
---"""

    messages = [{'role': 'system', 'content': system_prompt}]

    # Add recent chat buffer (last 3 exchanges, capped at 2,000 chars total)
    buffer_text = ""
    safe_buffer = []
    for msg in reversed(rolling_chat_buffer):
        if len(buffer_text) + len(msg['content']) < 2000:
            safe_buffer.insert(0, msg)
            buffer_text += msg['content']
        else:
            break
    messages.extend(safe_buffer)
    messages.append({'role': 'user', 'content': user_input[:2000]})

    start_inference = time.perf_counter()
    with inference_lock:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=messages,
            options={"num_ctx": NUM_CTX, "temperature": 0.2}
        )
    ai_answer = response['message']['content']
    end_inference = time.perf_counter()
    inference_time = end_inference - start_inference

    # Strip common AI self-referencing prefixes
    for prefix in ["AI:", "Assistant:", "Answer:"]:
        if ai_answer.lstrip().startswith(prefix):
            ai_answer = ai_answer.lstrip()[len(prefix):].strip()
            break

    # ── ASYNC SAVE ─────────────────────────────────────────────────────────
    # Save the conversation turn to ChromaDB in a background thread.
    # The chunk index is captured HERE (main thread) to avoid race conditions.
    saved_chunk_index = session_chunk_index
    session_chunk_index += 1

    def _save():
        start_save = time.perf_counter()
        try:
            combined_text = f"U: {user_input[:2000]}\nAI: {ai_answer}"
            memory_type = classify_memory(combined_text)
            entities = extract_entities(combined_text) if memory_type == "FACT" else ""
            collection.add(
                documents=[combined_text[:2000]],
                metadatas=[{
                    "type": memory_type,
                    "group_id": current_session_block_id,
                    "chunk_index": saved_chunk_index,
                    "entities": entities
                }],
                ids=[str(uuid.uuid4())]
            )
            save_time = time.perf_counter() - start_save
            print(f"   [PERF] Retrieval: {retrieve_time:.3f}s | Inference: {inference_time:.3f}s | Save: {save_time:.3f}s")
        except Exception as e:
            print(f"\n[Save Error] {e}")

    threading.Thread(target=_save, daemon=True).start()

    # Update rolling buffer (last 3 turns = 6 messages)
    rolling_chat_buffer.append({'role': 'user', 'content': user_input[:2000]})
    rolling_chat_buffer.append({'role': 'assistant', 'content': ai_answer})
    if len(rolling_chat_buffer) > 6:
        rolling_chat_buffer[:] = rolling_chat_buffer[-6:]

    timings = {"retrieval": retrieve_time, "inference": inference_time}
    return ai_answer, timings


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: STANDALONE INTERACTIVE MODE
# Run `python memory_engine.py` to use as a standalone chatbot
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AGENTIC RAG MEMORY ENGINE  —  Plug & Play Edition")
    print(f"  Model: {LLM_MODEL}  |  DB: {DB_PATH}")
    print("  Type 'exit' to quit. Memory is saved automatically.")
    print("="*60 + "\n")

    try:
        while True:
            check_vram()
            user_in = input("You: ").strip()
            if not user_in:
                continue
            if user_in.lower() in ['exit', 'quit', 'q']:
                break

            answer, timings = chat_logic(user_in)
            print(f"\nAI: {answer}")
            print(f"    [{timings['retrieval']:.2f}s retrieval | {timings['inference']:.2f}s inference]\n")

    except KeyboardInterrupt:
        pass

    print("\nSession saved to disk. Goodbye.")
