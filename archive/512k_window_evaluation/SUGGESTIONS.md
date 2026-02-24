# Future Optimizations: Achieving 100% Recall at 512k+ Contexts

The current architecture scores a 3/5 on a needle-in-a-haystack test across 2,000,000 characters (512k tokens). The vector search and agentic routing (Stages 1 and 2) work perfectly to find the exact historical block. 

The remaining point of failure is **Stage 3 Context Fatigue ("Lost in the Middle")**. When an 8,000-character conversational block is dumped into the constrained 4,000-token window of a local 3B parameter model, the LLM hallucinates or misses highly specific nouns and numbers during final inference.

Here are four advanced, highly experimental architectural suggestions to solve Stage 3 fatigue and hit 100% precision:

## 1. The "Skim & Squeeze" (Two-Pass Generation)
Instead of feeding the raw 8,000-character block directly into the final conversational answer prompt, we mandate a condensation step.
*   **Pass A (Extraction):** Feed the 8,000 characters to a fast sub-agent with the strict prompt: *"You are an extractor. Find every proper noun, number, and direct claim related to [User Query] in this text. Output ONLY a bulleted list. Do not answer the question."*
*   **Pass B (Synthesis):** We take that highly condensed bulleted list (which is now ~300 characters instead of 8,000) and feed *that* to the main conversational LLM to generate the final answer. 
*   **Why it works:** By distilling the context right before answering, you eliminate conversational noise and completely bypass "Lost in the Middle" syndrome.

## 2. Deep Metadata "Cheat Sheets" (Knowledge Graph Hybrid)
Currently, the system saves raw text into ChromaDB and only uses the LLM to classify it as FACT or CHATTER. We can force the classifier to also extract **Entities** before saving.
*   **The Ingestion:** When the user says, *"The budget is 850 million euros for Leviathan."* The system saves the text, but also adds a metadata array to ChromaDB: `entities: ["850 million euros", "Leviathan", "budget"]`
*   **The Exhumation:** When Stage 3 exhumes the conversational block, it also exhumes the raw `entities` array and pastes it at the very top of the LLM's prompt as a "Cheat Sheet". 
*   **Why it works:** The LLM doesn't have to hunt through 8,000 characters of prose; the exact hard metrics are pinned to the top of its vision, effectively acting as an attached Knowledge Graph.

## 3. Forced Chain-of-Thought (CoT) Verification
Small parameter models (like 3B) often rush to answer and skip reading the entire context window. We can physically force the model to allocate compute towards reading the context by requiring a `<think>` block.
*   **The Prompt:** We change the system prompt to explicitly demand: *"Before answering, you MUST write a `<think>` block. Inside that block, you must explicitly quote the text where you found the answer to each part of the user's question."*
*   **Why it works:** This forces the neural network to spend "compute tokens" searching its context window and verifying sources before it generates the final words, artificially boosting its reading comprehension.

## 4. Agentic "Ctrl-F" (Interactive Exhumation)
This is the most radical approach. Instead of dumping 8,000 characters on the LLM's lap and asking it to figure it out, we don't give it the text at all.
*   **The Tool:** We give the LLM a Python tool called `search_local_context(keyword)`. 
*   **The Process:** The LLM reads the user's question (*"What was the budget?"*), realizes it needs the data, and outputs an internal command: `search_local_context("budget")`. A fast Python regex searches the 8k exhumed block and returns just that single sentence to the LLM. 
*   **Why it works:** The LLM agentically navigates the retrieved memory block exactly like a human using `Ctrl-F` on a webpage. It only ever sees the exact sentences it requests, keeping the active context window astronomically lean.
