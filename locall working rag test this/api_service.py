import os
import sys
import uuid
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import aiohttp
import asyncio
# Ensure we can import the engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import memory_engine_parallel_lms as engine

app = FastAPI(title="Local Memory OpenAI-Compatible API")

# Allow CORS for Local Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- OpenAI Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Dict[str, Any] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

class IngestRequest(BaseModel):
    filename: str
    text: str

# --- ENDPOINTS ---

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: Request, body: ChatCompletionRequest):
    """
    OpenAI-compatible endpoint that injects local memory context.
    """
    # 1. Extract the last user message
    user_msg = ""
    for msg in reversed(body.messages):
        if msg.role == "user":
            user_msg = msg.content
            break
    
    if not user_msg:
        raise HTTPException(status_code=400, detail="No user message found in request.")

    print(f"📡 API Request: '{user_msg[:50]}...' (Local Offline Mode)")
    
    # 2. Call the Memory Engine (Retrieval + Local LLM Inference)
    try:
        answer, metrics = engine.chat_logic(user_input=user_msg)
        
        usage_data = metrics.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        
        # 3. Format as OpenAI Response
        return ChatCompletionResponse(
            model=body.model,
            usage=usage_data,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=answer)
                )
            ]
        )
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/ingest")
async def ingest_document(body: IngestRequest):
    """
    Ingest a whole document directly from the web interface.
    Slices into chunks, embeds via LM Studio, and stores in ChromaDB.
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty text payload.")
        
    print(f"📡 API Request: Ingesting '{body.filename}' (Length: {len(body.text)})")
    
    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 500
    
    text = body.text
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(f"[Source: {body.filename}]\n{chunk}")
        start += (CHUNK_SIZE - CHUNK_OVERLAP)
        
    print(f"   => Sliced into {len(chunks)} chunks. Pushing with 1000-CHUNK BATCHES...")
    
    collection = engine.get_collection()
    success_count = 0
    batch_size = 1000  # THE LIMIT: 1000 chunks per call
    semaphore = asyncio.Semaphore(4) # 4 batches mean 4000 chunks queued in GPU
    
    async def process_batch(session, batch_chunks):
        nonlocal success_count
        async with semaphore:
            try:
                payload = {
                    "model": "text-embedding-nomic-embed-text-v1.5@f32",
                    "input": batch_chunks
                }
                # Huge timeout for huge batches
                async with session.post("http://localhost:1234/v1/embeddings", json=payload, timeout=300) as resp:
                    emb_resp = await resp.json()
                    
                if "data" in emb_resp:
                    embeddings = [item["embedding"][:256] for item in emb_resp["data"]]
                    ids = [f"{body.filename}_{str(uuid.uuid4())}" for _ in range(len(batch_chunks))]
                    
                    collection.add(
                        documents=batch_chunks,
                        embeddings=embeddings,
                        ids=ids
                    )
                    success_count += len(batch_chunks)
                    print(f"      [MAX SPEED] {success_count}/{len(chunks)} chunks ingested...")
            except Exception as e:
                print(f"   [Limit Error] {e}")

    # Create batches
    chunk_batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]

    async with aiohttp.ClientSession() as session:
        tasks = [process_batch(session, b) for b in chunk_batches]
        await asyncio.gather(*tasks)
            
    print(f"✅ Ingestion Extreme Complete. {success_count}/{len(chunks)} chunks saved.")
    
    return {
        "status": "success", 
        "filename": body.filename, 
        "chunks_extracted": len(chunks),
        "chunks_inserted": success_count
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "engine": "10M-Token Local Offline Memory"}

# Mount the static frontend interface at the root
app.mount("/", StaticFiles(directory="hf_frontend", html=True), name="frontend")

if __name__ == "__main__":
    # Local port
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
