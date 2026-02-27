"""
🚀 Infinite Context RAG — QUICK START CHAT
══════════════════════════════════════════
A simplified, user-friendly interface for the Phase 16 Parallel Engine.
Optimized for LM Studio + high-precision fact extraction.
"""

import sys
import os
import time

# Ensure we can import the engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import memory_engine_parallel_lms as engine

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        INFINITE CONTEXT RAG — QUICK START CHAT       ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  1. Start LM Studio (Server tab)                         ║")
    print("║  2. Load a model (e.g., DeepSeek, Phi-4, Llama)          ║")
    print("║  3. Run INGEST_DATA.py (if you haven't yet)              ║")
    print("║  4. Type your question below                             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\n[!] Setup Note: Set LM Studio slots to 4-16 for best speed.")
    print("[!] Model Tip: Use reasoning models for best fact extraction.\n")

    while True:
        try:
            print("-" * 60)
            user_input = input("\n👤 YOU: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
                
            if not user_input:
                continue

            print("\n🔍 Thinking...")
            start_t = time.perf_counter()
            
            # Fire the high-precision parallel engine
            answer, timings = engine.chat_logic(user_input)
            
            end_t = time.perf_counter()
            total_t = end_t - start_t

            print(f"\n🤖 AI: {answer}")
            
            # Minimalist timing info
            print(f"\n[Stats] Pipeline: {total_t:.1f}s | Retrieval: {timings['retrieval']:.2f}s")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("Make sure LM Studio is running at http://localhost:1234")

if __name__ == "__main__":
    main()
