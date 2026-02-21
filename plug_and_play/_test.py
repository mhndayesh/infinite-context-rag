"""Quick functional test for plug_and_play/memory_engine.py"""
import sys, time
sys.path.insert(0, '.')
from memory_engine import chat_logic

print("=== PLUG & PLAY FUNCTIONAL TEST ===\n")

# Turn 1: store a unique fact
print("[1] Storing fact...")
a1, t1 = chat_logic("Please explicitly commit to memory: the test API key is PNP-DEMO-42 and the server port is 8877")
print(f"    AI: {a1[:200]}")
print(f"    Retrieval: {t1['retrieval']:.2f}s | Inference: {t1['inference']:.2f}s\n")

print("[*] Waiting 5s for async save to complete...")
time.sleep(5)

# Turn 2: recall the fact
print("[2] Recalling fact...")
a2, t2 = chat_logic("What is the test API key and what port does the server use?")
print(f"    AI: {a2[:300]}")
print(f"    Retrieval: {t2['retrieval']:.2f}s | Inference: {t2['inference']:.2f}s\n")

# Grade
recalled_key  = "PNP-DEMO-42" in a2
recalled_port = "8877" in a2

print("=== RESULTS ===")
print(f"  API key  PNP-DEMO-42 recalled: {'PASS' if recalled_key  else 'FAIL'}")
print(f"  Port     8877        recalled: {'PASS' if recalled_port else 'FAIL'}")
print(f"  Overall: {'PASS' if (recalled_key and recalled_port) else 'PARTIAL/FAIL'}")
