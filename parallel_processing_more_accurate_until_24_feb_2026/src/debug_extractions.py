"""
DEBUG: Ground Truth Extraction Check
════════════════════════════════════
This script fires parallel workers and prints the RAW 'cheat_sheet' 
before any final LLM filtering or refusal.
"""

import asyncio, os, sys, uuid
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import memory_engine_parallel_lms as engine

# 1. Setup a specific test case (Stage 3 logic)
NEEDLE_CODE = "SECRET-VALIDATION-999"
HAYSTACK = "The brown fox jumped. " * 500  # Some padding
NEEDLE = f" The reactor shutdown code is {NEEDLE_CODE}. "
FULL_TEXT = HAYSTACK[:2000] + NEEDLE + HAYSTACK[2000:]
QUESTION = "What is the reactor shutdown code?"

async def debug_check():
    print(f"\n--- DEBUG: STARTING RAW EXTRACTION CHECK ---")
    print(f"Target Needle: {NEEDLE_CODE}")
    
    # Fire parallel extraction directly
    # This bypasses Stage 1 (Retrieval) and Stage 3 (Final Answer)
    cheat_sheet = await engine.async_parallel_extract(FULL_TEXT, QUESTION)
    
    print(f"\n--- RAW CHEAT SHEET (FROM WORKERS) ---")
    if cheat_sheet:
        print(cheat_sheet)
        if NEEDLE_CODE in cheat_sheet:
            print(f"\n✅ GROUND TRUTH: The workers pulse-checked correctly! Code found in the extracts.")
        else:
            print(f"\n❌ GROUND TRUTH: The workers actually missed it.")
    else:
        print("\n❌ GROUND TRUTH: No facts extracted at all.")
    print(f"----------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(debug_check())
