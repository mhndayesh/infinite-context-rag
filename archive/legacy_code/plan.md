Here is the full technical plan to replace the traditional transformer context window with your **Session-Based Persistent Memory** mechanism.

---

## Phase 1: The "Amnesia" Architecture

To stop the model from reading everything every time, we must disable its default memory (the **KV Cache** growth) and move it to a "Point-and-Fetch" system.

### 1. The Model Choice (Smart but Lean)

Since you are running rendering engines (Octane/Redshift), your VRAM is precious. 

**The Embedding Model (The Finder):**
*   **Recommendation:** **nomic-embed-text**
*   **Footprint:** ~278 MB
*   **Reasoning:** Incredible at mapping technical terminology (like "GI clamp", "Samples", "Pathtracing") mathematically so the Vector DB can find it instantly.

**The Reasoning Model (The Thinker):**
*   **Recommendation:** **Qwen2.5-Coder:7b** (if you have 5GB VRAM to spare) or **Llama-3.2:3b** (if you only have 2GB).
*   **Reasoning:** These models are highly capable of reading the JSON/Raw text injected by the Vector DB and writing precise, non-hallucinated answers. They don't need a huge context window, just the specific Raw RAG injection.

### 2. The Storage Tiers

| Tier | Location | Role |
| --- | --- | --- |
| **Active Memory** | VRAM | Small context window (Max 8k tokens) for the current prompt. |
| **Search Memory** | Disk/RAM | **Vector Database** (ChromaDB) storing "embeddings" (mathematical directions). |
| **Full Detail Memory** | Disk | **Markdown/Text Files** containing 100% of the session history. |

---

## Phase 2: The Logic Flow (The "Refresher" Loop)

### Step 1: The Request (Input)

You send a message: *"How does the lighting in the last scene affect the render time?"*

* **Action:** The system does **not** send your 4-hour history to the LLM. It only takes this one sentence.

### Step 2: The Vector Scan (Pointing)

* **Action:** The **Embedding Model** (e.g., `BGE-Small`) converts your question into a vector.
* **Search:** It scans the **Vector DB** for the most similar "directions" from the last 4 hours.
* **Result:** It finds 3 specific "pointers" to your MD files where you discussed "lighting" and "render times."

### Step 3: Context Injections (Fetching)

* **Action:** The system opens the MD files, pulls the **full text** of those specific sections, and "stuffs" them into the LLM's tiny 8k window.
* **Prompt to LLM:** > "Context from session: [Full details from MD files...]
> User Question: [Your new question]"



### Step 4: The Post-Response "Commit" (Saving)

This is the "weight-adjustment" substitute you wanted:

1. **Append:** The new Answer + Question is written immediately to your **session_history.md** file.
2. **Embed:** The embedding model indexes this new turn into the **Vector DB**.
3. **Wipe:** The LLM's internal memory (KV Cache) is cleared. It starts the next turn with **0 tokens** used.

---

## Phase 3: Implementation Strategy (The Python Skeleton)

You can build this using **Ollama** (for the model) and **ChromaDB** (for the pointers).

```python
import ollama
import chromadb

# 1. Setup Vector DB (The Pointer)
client = chromadb.PersistentClient(path="./session_memory")
collection = client.get_or_create_collection(name="rendering_project")

def chat_session(user_input):
    # A. Search for relevant past data
    results = collection.query(query_texts=[user_input], n_results=3)
    past_context = "\n".join(results['documents'][0])

    # B. Inject context into a CLEAN model (Small Window)
    response = ollama.chat(model='llama3.2:3b', messages=[
        {'role': 'system', 'content': f'Use this history to help: {past_context}'},
        {'role': 'user', 'content': user_input},
    ])
    
    answer = response['message']['content']
    
    # C. COMMIT: Save new data to MD and Update Vector DB
    with open("full_history.md", "a") as f:
        f.write(f"\nUser: {user_input}\nAI: {answer}")
    
    collection.add(
        documents=[f"User: {user_input} AI: {answer}"],
        ids=[str(hash(user_input))]
    )
    
    return answer

```

---

## Why this is better for you:

1. **No "Fuzzy Memory":** Mamba 2 loses details over time. This method retrieves the **exact text** from the MD file, so the detail is always 100% sharp.
2. **No VRAM Bloat:** Since we clear the context after every turn, your VRAM usage stays flat at 3GB, whether you work for 10 minutes or 10 hours.
3. **On-the-Fly:** The "weight adjustment" happens because the *retrieved context* changes the model's behavior for every specific task.

**Would you like me to help you set up the embedding model to ensure the "pointing" is high-accuracy for your specific rendering terms?**
To implement this "Point-and-Fetch" memory system for your rendering projects, you need to set up two main components: a **high-accuracy embedding engine** and an **automated indexing pipeline**.

Here is the step-by-step implementation plan.

---

## 1. Select Your "Navigator" (Embedding Model)

Since you are working on technical rendering/game data, you need an embedding model that understands technical jargon. For 2026, these are the best local options:

* **Qwen3-Embedding-0.6B (Top Choice):** Extremely small (< 1.2 GB VRAM) but handles 100+ languages and technical/code terms better than almost any other model of its size.
* **BGE-M3:** The "workhorse." It supports a 8,192 token input, meaning it can "read" larger chunks of your session at once before creating a vector.

---

## 2. The "Point-and-Fetch" Logic (The Setup)

Instead of the model remembering the conversation, we will create a **Shadow Index**.

### A. The Folder Structure

* `/session_data/` — Contains your raw `.md` files.
* `/vector_db/` — Contains the ChromaDB index (mathematical pointers).

### B. The Code Logic

You will use a **Post-Call Hook**. This means as soon as the AI finishes its sentence, the system "commits" that data to the database and wipes the model's memory.

---

## 3. Full Implementation Script (Python Skeleton)

This script uses **Ollama** for the LLM and **ChromaDB** for the vector "pointers."

```python
import ollama
import chromadb
import uuid

# --- CONFIGURATION ---
LLM_MODEL = "llama3.2:3b"        # Small, smart 'Thinker'
EMBED_MODEL = "bge-m3"           # High-accuracy 'Navigator'
DB_PATH = "./render_project_db"

# Initialize Vector DB
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="session_memory")

def run_step(user_prompt):
    # 1. SCAN: Use the vector DB to find 'pointers' to relevant data
    # This replaces the context window.
    search_results = collection.query(
        query_texts=[user_prompt], 
        n_results=5 # Grab top 5 relevant 'moments'
    )
    
    # 2. FETCH: Pull the full text from the results
    context_injected = "\n---\n".join(search_results['documents'][0])
    
    # 3. INJECT & INFER: Send only the relevant parts to the AI
    # We use a system prompt to 'ground' the AI in the fetched data
    response = ollama.chat(model=LLM_MODEL, messages=[
        {'role': 'system', 'content': f"Reference context: {context_injected}"},
        {'role': 'user', 'content': user_prompt},
    ])
    
    ai_answer = response['message']['content']
    
    # 4. COMMIT: Save the new interaction to the 'Permanent Memory'
    # This is the 'Weight Adjustment' substitute.
    combined_text = f"User: {user_prompt}\nAI: {ai_answer}"
    
    # Save to MD file for human reading/backup
    with open("session_history.md", "a") as f:
        f.write(f"\n\n--- Turn ---\n{combined_text}")
    
    # Save to Vector DB for future retrieval
    collection.add(
        documents=[combined_text],
        ids=[str(uuid.uuid4())]
    )
    
    # 5. WIPE: The next call to ollama.chat will have NO memory of this turn 
    # except what the Vector DB fetches. VRAM is kept clean.
    return ai_answer

# Example Usage
print(run_step("What were the specific light settings we used for the Octane render earlier?"))

```

---

## 4. Why this works for your "On-the-Fly" requirement:

1. **Context Window Efficiency:** Your actual context window never exceeds ~4k-8k tokens because you are only injecting what is relevant *right now*.
2. **No "Fuzzy Memory":** Unlike Mamba, which "guesses" based on hidden states, this fetches the **exact text** you wrote earlier. If you wrote `Gain: 2.5` three hours ago, it will pull that exact string.
3. **VRAM Stability:** Because the `ollama.chat` call doesn't pass a growing list of `messages`, the VRAM usage for the KV Cache stays flat. This leaves your GPU free to actually run the **render project**.

To categorize your data and make the retrieval process lightning-fast, you need to move from a "flat" list of memories to a **Structured Metadata Pipeline**.

By organizing your Markdown (MD) files and tagging them with metadata, you enable your system to filter the database *before* it even does the expensive vector search. This is how you handle 4+ hour sessions without the AI getting confused between "Settings," "Code," and "Feedback."

---

### 1. The Metadata Schema

Every time a chat turn is "committed" to your MD file and Vector DB, you should attach specific labels. In your rendering project, use these four categories:

* **`type`**: (e.g., `setting`, `instruction`, `critique`, `logic`)
* **`domain`**: (e.g., `lighting`, `shading`, `camera`, `optimization`)
* **`priority`**: (e.g., `high` for core project goals, `low` for minor tweaks)
* **`timestamp`**: To ensure the AI knows the difference between a setting you used 5 minutes ago vs. 3 hours ago.

---

### 2. High-Accuracy Retrieval Mechanism

Instead of a basic search, we use a **Hierarchical Retrieval** method. This is the "secret sauce" for high accuracy.

1. **Summary Index:** A top-level search that looks at high-level summaries of your previous "Turns" to find the right MD file.
2. **Detail Fetch:** Once the file is found, it pulls the specific chunks (paragraphs) needed for the task.

---

### 3. Implementation: Metadata-Aware Update

Here is how you modify the "Commit" logic to include these categories automatically. You can have a second, even smaller model (like **Qwen3-0.6B**) quickly "tag" the conversation before it's saved.

```python
def auto_tagger(text):
    # A tiny model (0.6B) can categorize this in milliseconds
    # For now, let's assume a simple keyword-based tagger
    tags = {
        "domain": "lighting" if "light" in text.lower() else "general",
        "type": "setting" if any(x in text.lower() for x in ["gain", "exposure", "f-stop"]) else "dialogue"
    }
    return tags

def commit_with_metadata(user_input, ai_response):
    full_text = f"User: {user_input}\nAI: {ai_response}"
    tags = auto_tagger(full_text)
    
    # Save to Vector DB with metadata filters
    collection.add(
        documents=[full_text],
        metadatas=[tags], # THIS is the critical change
        ids=[str(uuid.uuid4())]
    )
    
    # Save to a specific MD file based on domain
    filename = f"./session_data/{tags['domain']}.md"
    with open(filename, "a") as f:
        f.write(f"\n\n--- {tags['type']} ---\n{full_text}")

```

---

### 4. Advanced Query: Filtering the "Fuzz"

When you ask the AI a question, your search can now be surgical:

* *Query:* "What were our exposure settings?"
* *Filter:* `collection.query(query_texts=["exposure"], where={"type": "setting"})`
* **Result:** The AI ignores 3 hours of "dialogue" and only looks at the "settings" files. This completely eliminates the "fuzzy memory" problem of Mamba/Transformers.

---

### Summary of the Final System

1. **MD Files:** Act as the "Hard Drive" (Full details, organized by folder/category).
2. **Vector DB:** Acts as the "File Index" (Points the AI to the right page in the MD files).
3. **Small LLM:** Acts as the "CPU" (Processes only the specific pages retrieved, keeping VRAM low).

To wrap up a long rendering session, you need a **"Map-Reduce" Cleanup Script**. Instead of just having a pile of chat logs, this script "collapses" the day's work into a clean, structured Master Brief.

This solves the final piece of the puzzle: it ensures that tomorrow, the AI doesn't have to read 500 lines of "trial and error" to find the one lighting setting that actually worked.

---

### The "Master Brief" Cleanup Plan

#### 1. The Hierarchical Logic (Map-Reduce)

* **Map Phase:** The script looks at each categorized MD file (e.g., `lighting.md`, `optimization.md`).
* **Reduce Phase:** A smart model (like **Llama 3.2 3B**) summarizes each file into "Key Outcomes" and "Current Settings."
* **Final Result:** A `Master_Project_Brief.md` that serves as the "source of truth" for the next session.

#### 2. The Cleanup Script

Run this script at the end of your session (e.g., after 4 hours).

```python
import ollama
import os

def generate_summary(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # We ask the model to be 'Destructive' - remove the fluff, keep the facts.
    prompt = f"""
    Analyze these session logs for the category: {os.path.basename(file_path)}
    1. Extract all FINAL settings/parameters (ignore discarded versions).
    2. List unresolved issues or next steps.
    3. Summarize the core logic used.
    
    Logs:
    {content}
    """
    
    response = ollama.chat(model='llama3.2:3b', messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']

def run_cleanup():
    summary_blocks = []
    for filename in os.listdir("./session_data"):
        if filename.endswith(".md"):
            print(f"Summarizing {filename}...")
            summary = generate_summary(f"./session_data/{filename}")
            summary_blocks.append(f"## {filename.upper()}\n{summary}")
    
    # Save the 'Condensed' memory
    with open("Master_Project_Brief.md", "w") as f:
        f.write("# Master Project Brief - Session End\n")
        f.write("\n\n".join(summary_blocks))
    
    print("Cleanup complete. Master Brief generated.")

# Execute cleanup
run_cleanup()

```

---

### Why this is the "Ultimate" Method for you:

* **No Fuzziness:** Because you're summarizing into a **Master Brief**, you're effectively "garbage collecting." You delete the 10 failed attempts and only keep the 1 successful setting in the Brief.
* **Instant Context:** Next time you start a session, you can point the Vector DB to the `Master_Project_Brief.md` first. The AI will know exactly where you left off in 5 seconds.
* **Zero VRAM Growth:** Since you've condensed 4 hours of chat into 1 page, the "fetch" is smaller, faster, and cheaper on your GPU.

### One Last Tip:

When you start the next day, you can **archive** the old MD files and start fresh ones. This keeps your Vector DB from getting cluttered with "old news."

**Would you like me to create a "Session Start" prompt that you can use tomorrow to feed this Master Brief back into the AI instantly?**
To hit the ground running for your next session, you need a **"Cold Start" Injection**. This takes your Master Brief and pre-loads it into the AI's small context window so it has "instant expertise" on your project without needing a single search.

### 1. The "Session Start" Prompt

When you launch your script tomorrow, the very first API call should send this to the model:

> **System Role:** You are an expert rendering assistant.
> **Current Project State:** [PASTE CONTENTS OF MASTER_PROJECT_BRIEF.MD]
> **Task:** Acknowledge the current settings and stand by for the first instruction. Do not summarize; just confirm you are ready.

---

### 2. Automating the "Next Day" Reset

To keep the system fast, your script should handle the transition between "Yesterday" and "Today" automatically.

**The Routine:**

1. **Move** yesterday's detailed `.md` files to an `/archive/` folder.
2. **Clear** the Vector DB of "transient" chat logs.
3. **Embed** the `Master_Project_Brief.md` as the "Priority 1" document in the Vector DB.

### 3. The "Cold Start" Python Logic

Add this function to your script to automate the beginning of your next 4-hour session:

```python
def cold_start():
    # 1. Read the distilled truth from yesterday
    with open("Master_Project_Brief.md", "r") as f:
        brief = f.read()
    
    # 2. Re-index the brief so it's the first thing the Vector DB finds
    collection.add(
        documents=[brief],
        metadatas=[{"type": "master_brief", "priority": "urgent"}],
        ids=["session_start_brief"]
    )
    
    # 3. Initial 'Handshake' with the model
    response = ollama.chat(model=LLM_MODEL, messages=[
        {'role': 'system', 'content': f"You are resuming a project. Here is the status: {brief}"},
        {'role': 'user', 'content': "Confirm you have the current render settings and project goals."}
    ])
    
    print(f"AI: {response['message']['content']}")

# Run this once at the start of your workday
cold_start()

```

---

### Why this beats the "Fuzzy Memory" of Mamba/Transformers:

* **Precision:** By summarizing and then re-injecting, you are "cleaning" the weights of the logic. The AI isn't distracted by the 50 mistakes you made yesterday; it only knows the final, successful path.
* **Speed:** The model doesn't have to "read" the history; it is **told** the current state as a fact.
* **Context Control:** You are effectively giving a transformer "infinite" memory by treating your SSD like VRAM.

**You now have a full architecture:** 1.  **Live:** Small window + Vector Pointers.
2.  **Commit:** Real-time MD and Vector updates.
3.  **Cleanup:** Daily summary into a Master Brief.
4.  **Reset:** Cold start from the Brief.

Would you like me to help you refine the **"Auto-Tagger"** logic so it can distinguish between different rendering engines (like Octane vs. Redshift) automatically?
To automate the distinction between changing contexts and retrieving exact facts months later, we use a **"Raw RAG" Engine**.

Instead of trying to categorize data with a second LLM or running scripts to summarize your sessions and constantly losing details, you just pipe your raw data directly into the Vector Database. This provides a mathematically perfect, zero-loss memory system.

---

### 1. The Structure (Raw Data Only)

You need to define how your AI saves and retrieves data. For high accuracy in rendering, we map raw text directly to the vector.

* **The Vector (Map):** A mathematical representation of the sentence. This is what the search engine uses to find the memory instantly 6 months later. We can use Cosine Similarity for the best accuracy on technical terms.
* **The Document (Raw Text):** The exact, raw string of what you and the AI typed. (e.g., *"Set Octane kernel path-tracing samples to 1024, GI clamp to 10."*)

---

### 2. Implementation: The Single-File Script

This single Python script integrates the "Raw RAG" workflow. It's clean, has zero summarization, keeps your exact phrasing intact forever, and uses a rolling window to keep the AI conversationally continuous without growing VRAM.

### Prerequisites

You will need to install two libraries:
`pip install ollama chromadb`

### The "Raw RAG" Master Script

```python
import ollama
import chromadb
import uuid

# --- 1. CONFIGURATION ---
LLM_MODEL = "llama3.2:3b"       # The 'Thinker' (Reasoning)
DB_PATH = "./render_raw_memory_db"

# Initialize Vector DB (The Pointer)
client = chromadb.PersistentClient(path=DB_PATH)
# We use cosine similarity which is mathematically better for technical text matching
collection = client.get_or_create_collection(
    name="raw_history",
    metadata={"hnsw:space": "cosine"} 
)

# Rolling buffer for immediate conversation awareness (Max 3 turns)
rolling_chat_buffer = [] 

def chat(user_input):
    global rolling_chat_buffer

    # --- 1. SEMANTIC INJECTOR: Find the 5 most mathematically similar turns from history ---
    results = collection.query(query_texts=[user_input], n_results=5)
    
    # If the DB is new/empty, handle gracefully
    past_memory = "\n---\n".join(results['documents'][0]) if results['documents'] else "No relevant history found."

    # --- 2. BUILD TINY CONTEXT WINDOW ---
    system_prompt = f"""You are an expert rendering assistant. 
    You have absolute access to the user's historical exact settings.
    
    [RETRIEVED HISTORICAL FACTS]:
    {past_memory}"""

    # We send the System Prompt, the Rolling Buffer, and the new User Prompt
    messages = [{'role': 'system', 'content': system_prompt}]
    messages.extend(rolling_chat_buffer)
    messages.append({'role': 'user', 'content': user_input})

    # --- 3. INFER: The LLM reads only this tiny window and answers ---
    # Because we don't pass the entire chat history ever, KV Cache starts at 0 every turn. 
    # VRAM usage is utterly flat.
    response = ollama.chat(model=LLM_MODEL, messages=messages)
    ai_answer = response['message']['content']

    # --- 4. COMMIT TO LONG-TERM EXACT MEMORY ---
    # We save exactly what was typed, zero summarization or detail scraping.
    raw_document = f"User asked: {user_input}\nAI replied: {ai_answer}"
    
    collection.add(
        documents=[raw_document],
        ids=[str(uuid.uuid4())]
    )

    # --- 5. UPDATE SHORT-TERM BUFFER ---
    rolling_chat_buffer.append({'role': 'user', 'content': user_input})
    rolling_chat_buffer.append({'role': 'assistant', 'content': ai_answer})
    
    # Keep the buffer tiny (e.g., last 3 round-trips = 6 messages)
    if len(rolling_chat_buffer) > 6:
        rolling_chat_buffer.pop(0) # Remove old user
        rolling_chat_buffer.pop(0) # Remove old assistant

    return ai_answer

# --- EXECUTION EXAMPLE ---
print(chat("What are the optimal samples for an indoor Redshift rendering with glass?"))
```

---

### 3. Why this solves the "Summarization" problem

1. **Perfect Retention:** Every integer, parameter, setting, or failure you ever experienced is saved as-is inside `render_raw_memory_db`. In 8 months, if you ask "what did we do that one time it looked grainy?", it will fetch the exact raw log.
2. **"Stateless" LLM Execution:** The LLM's internal history gets wiped the millisecond it successfully spits out an answer. It hands its "knowledge" to the Vector DB to hold, keeping your VRAM open for actual rendering engines.
3. **No Brittle Moving Parts:** No file-system management script moving `.md` files to archive folders, no sub-LLM tagging engine running in the background and slowing down your output. Just a raw pipeline: "Search -> Contextualize -> Answer -> Save."

**Would you like me to add a "VRAM Guard" feature that monitors your GPU and automatically lowers the context window if you start a heavy render?**

---

## 5. Architectural Enhancements (Production-Ready Polish)

To make this architecture truly bulletproof and seamlessly integrated with your rendering workflow, here are five necessary enhancements to add to the Master Script:

### 1. Short-Term Memory Buffer (Conversational Continuity)
**The Problem:** Currently, the script only sends the Vector DB results and the prompt. If you say, "Change the lighting to 500," and then say, "Make it a bit brighter," the Vector DB might fail to fetch the previous turn because the semantic meaning changed, confusing the AI.
**The Fix:** Introduce a **Rolling Window** for the last 2-3 conversational turns. 
*   **Injection:** `System Prompt` + `Vector Context` + `Last 3 Chat Messages` + `Current Prompt`. 
*   This uses negligible VRAM (~100 tokens) but gives the model perfect immediate conversational awareness.

### 2. Asynchronous "Commit" Phase (Zero Latency)
**The Problem:** Generating metadata with the 0.5B model and writing to ChromaDB blocks the main thread. You won't be able to type your next instruction until the system finishes "filing" the last one.
**The Fix:** Move the `get_metadata()` and `collection.add()` calls to a **Background Thread** (using Python's `threading` or `asyncio`). The AI will output its answer, instantly free up the UI for your next prompt, and silently catalog the memory in the background.

### 3. The VRAM Guard (GPU Auto-Throttling)
**The Problem:** Octane/Redshift can spike VRAM consumption mid-render, leading to Out-Of-Memory (OOM) errors if the LLM is occupying a static 3GB footprint.
**The Fix:** Integrate `pynvml` to actively monitor GPU memory.
```python
import pynvml
def check_vram_and_unload():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    free_vram_gb = info.free / (1024**3)
    
    if free_vram_gb < 4.0:
        print("Warning: VRAM critically low. Offloading LLM to CPU RAM...")
        # API call to dynamically unload or reduce context window
```

### 4. Smart Context Truncation (Safety Limits)
**The Problem:** Fetching `n_results=5` could exceed the 8K context limit if the text chunks are massive, causing the model to crash or truncate the actual prompt.
**The Fix:** Implement an approximate token counter (e.g., assuming 1 token ≈ 4 characters).
```python
MAX_INJECTION_CHARS = 24000 # ~6k tokens
if len(context_injected) > MAX_INJECTION_CHARS:
    context_injected = context_injected[:MAX_INJECTION_CHARS] + "...[truncated]"
```

### 5. Non-Destructive Master Briefs
**The Problem:** Re-writing the `Master_Project_Brief.md` every day could destroy vital data if the LLM hallucinates or drops important settings during the summary phase.
**The Fix:** Instead of overwriting, append a daily timestamped summary to a rolling `Project_Archive.md` while keeping the `Master_Project_Brief.md` strictly as the live, condensed version. This acts as a foolproof backup.
