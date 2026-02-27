import os
import sys
import re
import random
import time
import json
import uuid

# Ensure we can import the engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_engine_parallel_lms as engine

DATA_FILE = r"c:\tmp\niah_test_512k.txt"
LOG_FILE = r"c:\tmp\local_offline_memory\results\natural_conversation_log.md"

def extract_20_questions():
    print("🔍 Extracting 20 facts for the natural flow test...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    total_len = len(content)
    test_cases = []
    
    # Generate 20 random points
    for _ in range(20):
        start = random.randint(0, total_len - 10000)
        window = content[start:start+10000]
        # Find clean sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', window) if 80 < len(s) < 250 and '<' not in s and "NEEDLE" not in s]
        if sentences:
            fact = random.choice(sentences)
            test_cases.append(fact)
    
    # Always include the Project Orion needle for one of the 20
    test_cases.append("What is the launch code for project Orion, and who authorized it?")
    random.shuffle(test_cases)
    return test_cases[:20]

def run_natural_test():
    questions = extract_20_questions()
    collection = engine.get_collection()
    
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("# 🗨️ Natural Conversation & Logic Adjudication Log\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Engine**: InfiniteMemory (Turbo Batch v2)\n\n---\n")

    for i, q in enumerate(questions, 1):
        print(f"\n[Question {i}/20] Processing...")
        
        # 1. DB RECALL
        results = collection.query(query_texts=[q[:500]], n_results=6)
        candidates = results['documents'][0] if results['documents'] else []
        
        # 2. FORMATTING CANDIDATES
        formatted_candidates = []
        for idx, c in enumerate(candidates):
            formatted_candidates.append(f"[Candidate {idx+1}]\n{c}")
        
        context_block = "\n---\n".join(formatted_candidates)
        
        # 3. LLM INTERACTION
        # We call the engine's chat_logic directly to get the actual system output
        # but we also log the candidates ourselves for the report.
        answer, metrics = engine.chat_logic(q)
        
        # 4. LOGGING
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"## ❓ Question {i}: {q}\n\n")
            f.write("### 🗄️ Database Recall (Top-6 Candidates)\n")
            for cand in formatted_candidates:
                lines = cand.split('\n')
                label = lines[0]
                text_preview = lines[1][:500] if len(lines) > 1 else ""
                f.write(f"#### {label}\n")
                f.write(f"```text\n{text_preview}...\n```\n")
            
            f.write("\n### 🤖 AI Reasoning & Decision\n")
            f.write(f"**Final Answer**:\n{answer}\n")
            f.write(f"\n*Latency: {metrics.get('latency', 'N/A')} | Tokens: {metrics.get('usage', {}).get('total_tokens', 0)}*\n")
            f.write("\n---\n")
            
        print(f"✅ Question {i} complete.")
        time.sleep(1) # Small delay for LM Studio stability

    print(f"\n✨ Benchmark Finished! View the full chain of thought here:\n{LOG_FILE}")

if __name__ == "__main__":
    run_natural_test()
