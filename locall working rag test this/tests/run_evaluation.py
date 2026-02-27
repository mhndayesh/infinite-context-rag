import os
import sys
import json
import time
import random
import re
import asyncio
import aiohttp

# Ensure we can import the engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_engine_parallel_lms as engine

# The file is in c:\tmp\niah_test_512k.txt based on previous creation logs
DATA_FILE = r"c:\tmp\niah_test_512k.txt"
RESULTS_FILE = r"c:\tmp\local_offline_memory\results\evaluation_report.md"

async def run_eval():
    print("🚀 Starting Automated 512k NIAH Evaluation...")
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    total_len = len(content)
    # Generate 15 points across depths (0% to 95%)
    depths = [i/15 for i in range(15)]
    
    test_cases = []
    print(f"🔍 Extracting 15 facts from {total_len/1024/1024:.2f} MB file...")
    
    for depth in depths:
        start_idx = int(total_len * depth)
        search_window = content[start_idx : start_idx + 5000]
        
        # Look for fact sentences (avoiding needle)
        valid_sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', search_window) if 50 < len(s) < 250 and '<' not in s and '\n' not in s and "NEEDLE" not in s]
        
        if not valid_sentences:
             fact = "The launch code for project Orion is 'Delta-Seven-Tango'."
        else:
            fact = random.choice(valid_sentences)
            
        test_cases.append({
            "depth": f"{depth*100:.1f}%",
            "fact": fact,
            "query": fact[:100]
        })

    # Prepare report header
    report = []
    report.append("# 📊 512k Context Retrieval Evaluation Report")
    report.append(f"\n- **Dataset**: `niah_test_512k.txt` ({total_len/1024/1024:.2f} MB)")
    report.append(f"- **Total Tokens (Estimated)**: ~25M-30M")
    report.append(f"- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n| Depth | Fact/Needle Preview | Status | Latency | Top-1 Chunk Preview | Score |")
    report.append("|-------|---------------------|--------|---------|---------------------|-------|")

    print("\n⚡ Initializing Engine & Collection...")
    collection = engine.get_collection()

    print("\n⚡ Starting Retrieval Benchmark...")
    
    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/15] Testing Depth {test['depth']}...")
        start_time = time.time()
        
        # Direct Chroma Query
        results = collection.query(query_texts=[test['query']], n_results=5)
        latency = time.time() - start_time
        
        status = "❌ FAIL"
        top_preview = "N/A"
        match_score = 0
        
        if results['documents'] and results['documents'][0]:
            top_doc = results['documents'][0][0]
            top_preview = top_doc[:100].replace('\n', ' ') + "..."
            
            # Simple keyword overlap scoring
            keywords = [w.lower() for w in re.findall(r'\w{5,}', test['fact'])]
            matches = sum(1 for k in keywords if k in top_doc.lower())
            match_score = (matches / len(keywords)) if keywords else 0
            
            if match_score > 0.6:
                status = "✅ PASS"
        
        report.append(f"| {test['depth']} | {test['fact'][:50]}... | {status} | {latency:.2f}s | {top_preview} | {match_score:.1%} |")

    report.append("\n---")
    report.append("## 📜 Detailed Execution Logs (Top-1 Evidence)")
    for i, test in enumerate(test_cases, 1):
        report.append(f"\n### Test {i}: Depth {test['depth']}")
        report.append(f"- **Target Fact**: {test['fact']}")
        
        results = collection.query(query_texts=[test['query']], n_results=1)
        if results['documents'] and results['documents'][0]:
            report.append(f"- **Retrieved Top-1**: \n```text\n{results['documents'][0][0]}\n```")
        else:
            report.append("- **Retrieved Top-1**: NOTHING_FOUND")

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"\n✅ Evaluation Complete! Report saved to {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(run_eval())
