import memory_engine
import time

# Pre-warm BM25 index
memory_engine.sync_global_bm25(force=True)
print("\n--- PHASE XV: LIVE SPEED BENCHMARK ---")

# Test with async extraction ENABLED (default)
memory_engine.ASYNC_EXTRACTION_ENABLED = True
t = time.perf_counter()
answer, timings = memory_engine.chat_logic("What is the secret password to unlock the core mainframe?")
total_async = time.perf_counter() - t
print(f"\n[ASYNC ON]  Retrieval: {timings['retrieval']:.2f}s | Inference: {timings['inference']:.2f}s | Total: {total_async:.2f}s")
print(f"Answer: {answer[:150]}")

# Test with async extraction DISABLED (baseline)
memory_engine.ASYNC_EXTRACTION_ENABLED = False
t = time.perf_counter()
answer2, timings2 = memory_engine.chat_logic("What is the secret password to unlock the core mainframe?")
total_baseline = time.perf_counter() - t
print(f"\n[ASYNC OFF] Retrieval: {timings2['retrieval']:.2f}s | Inference: {timings2['inference']:.2f}s | Total: {total_baseline:.2f}s")
print(f"Answer: {answer2[:150]}")

print(f"\n--- SUMMARY ---")
print(f"Speed delta: {total_baseline - total_async:.2f}s saved with async extraction")
print(f"Both answers match: {('ALBATROSS' in answer) == ('ALBATROSS' in answer2)}")
