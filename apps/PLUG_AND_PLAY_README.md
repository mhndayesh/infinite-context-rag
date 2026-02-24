# 🚀 Infinite Context RAG: Plug-and-Play Guide

Welcome! This folder contains a high-precision, parallel-processing "Memory Engine" that lets you chat with millions of characters of data without losing accuracy.

## 🌟 Why use this version?
Most AI systems suffer from "Lost in the Middle" (they forget facts in large documents) or "Safety Refusal" (they refuse to tell you passwords or secret codes they found).

**This system solves both:**
1. **Parallel Scan:** It scans your documents in multiple batches at once (like having 16 librarians searching the shelves simultaneously).
2. **Direct-Return Bypass:** If our "librarians" find a specific code or fact, the engine returns it to you **directly** without letting the AI filter it out.

---

## 🛠 Setup (3 Easy Steps)

### 1. Start LM Studio
- Open **LM Studio**.
- Go to the **Server tab** (the `<->` icon).
- Load a reasoning model (like **DeepSeek-R1-Distill-Qwen-7B** or **Phi-4**).
- **Crucial:** Set your "Server Slots" to **16** (or as many as your GPU can handle) and "Context Length" to **8192**.
- Click **Start Server**.

### 2. Add Your Data (Build Your Database)
- Open the `source_docs` folder.
- Drop any `.txt` files you want to search through into that folder.
- Run the ingestion script:
```bash
python INGEST_DATA.py
```

### 3. Install Requirements & Chat
- Run: `pip install -r requirements.txt` (only need to do this once).
- Start chatting:
```bash
python QUICK_START_CHAT.py
```

---

## ⚙️ Advanced Settings (VRAM vs Speed)
If your computer is slowing down or crashing, open `memory_engine_parallel_lms.py` and adjust these:

- `MAX_CONCURRENT_WORKERS`: Reduce this to `4` if you have a smaller GPU (8GB VRAM). Keep it at `16` for high-end GPUs.
- `USER_CONTEXT_WINDOW`: Set this to match your LM Studio setting.

---

## 📝 Folder Contents
- `QUICK_START_CHAT.py`: The easiest way to interact with the engine.
- `INGEST_DATA.py`: Use this to add your own .txt files to the database.
- `source_docs/`: Drop your text files here before running the ingestor.
- `memory_engine_parallel_lms.py`: The high-performance core engine.
- `integrity_check.py`: Run this if you want to verify that the system is 100% honest and accurate.
- `benchmark_lm_studio.py`: Performance testing for large-scale data (512k tokens).
