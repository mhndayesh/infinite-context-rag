"""
Phase XVI: LM Studio Parallel Benchmark
───────────────────────────────────────
Verifies progress by running the new parallel engine against LM Studio.
"""

import sys, os, time, json, shutil, asyncio

# Use the Phase XVI parallel engine
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import memory_engine_parallel as engine

# Configuration for vLLM
engine.OPENAI_API_BASE = "http://localhost:8000/v1"
engine.LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

QUESTION = "What is the secret magical password to unlock the core mainframe?"
EXPECTED = "ALBATROSS-9000"

async def run_benchmark():
    print(f"--- Phase XVI: vLLM Parallel Benchmark ---")
    print(f"Connecting to: {engine.OPENAI_API_BASE}")
    print(f"Parallel Extraction: ENABLED")
    print(f"Total tokens in context: ~8,000 (4 chunks)")
    
    start = time.perf_counter()
    try:
        # In a real run, you'd have chunks in the DB.
        # Here we mock retrieving 4 large chunks to test the MAP-REDUCE speed.
        chunks = [
            "This is random filler text about system architecture... " * 100,
            "The security protocol requires a special code... " * 100,
            "The secret magical password to unlock the core mainframe is ALBATROSS-9000. " * 50,
            "Authentication failed. Please try the secondary backup code... " * 100
        ]
        
        # Manually trigger the parallel extraction part
        raw_context = "\n---\n".join(chunks)
        cheat_sheet = await engine.async_parallel_extract(raw_context, QUESTION)
        
        # Final answer
        prompt = f"Answer the question based on the context:\n{cheat_sheet}\n{raw_context}"
        response = await engine.async_openai.chat.completions.create(
            model=engine.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        
        total_time = time.perf_counter() - start
        passed = EXPECTED.lower() in answer.lower()
        
        print(f"\nRESULTS:")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Accuracy: {'✅ PASS' if passed else '❌ FAIL'}")
        print(f"  Answer: {answer[:100]}...")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        print("\nNOTE: Ensure vLLM server is running (docker logs -f vllm).")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
