import os
import sys
import time
import uuid
import shutil
import json
import logging
from datetime import datetime

# Silence noisy external libraries
import warnings
warnings.filterwarnings("ignore")
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)

# Setup our own integrity logger
integrity_log = logging.getLogger("integrity_proof")
integrity_log.setLevel(logging.DEBUG)
fh = logging.FileHandler("evaluation_integrity.log", mode='w', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
fh.setFormatter(formatter)
integrity_log.addHandler(fh)

import memory_engine

def run_512k_eval():
    integrity_log.info("="*60)
    integrity_log.info(" STARTING 512K TOKEN (2M CHAR) SESSION EVALUATION ")
    integrity_log.info("="*60)
    
    print("="*60)
    print("  PHASE X: 512k TOKEN (2M CHAR) SESSION MEMORY STRESS TEST  ")
    print("="*60)

    # 1. Reset Database
    if os.path.exists(memory_engine.DB_PATH):
        shutil.rmtree(memory_engine.DB_PATH)
        integrity_log.info(f"[SECURE START] Cleared entire vector database at {memory_engine.DB_PATH}")
        print("[DB Reset] Cleared database for a completely clean 512k run.")
    
    collection = memory_engine.get_collection()

    # 2. Load the 5 Target Sessions
    with open("data_samples/eval_sessions.json", "r", encoding="utf-8") as f:
        session_data = json.load(f)
    target_sessions = session_data["target_sessions"]

    # We want ~820 blocks (2500 chars each) = ~2,000,000 characters (approx 512k tokens)
    TOTAL_NOISE_BLOCKS = 820
    CHARS_PER_BLOCK = 2500
    
    # Map out the exact block indices where targets will be injected
    injection_schedule = {
        100: target_sessions[0], # Alpha
        250: target_sessions[1], # Bravo
        400: target_sessions[2], # Charlie
        550: target_sessions[3], # Delta
        700: target_sessions[4]  # Echo
    }

    print("\n--- INGESTION PHASE (~512,000 Tokens) ---")
    start_time = time.time()
    
    # Read text files from dataset512k
    dataset_dir = "dataset512k"
    all_text = ""
    if os.path.exists(dataset_dir):
        for root, _, files in os.walk(dataset_dir):
            for file in files:
                if file.endswith(('.txt', '.md', '.csv')):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            all_text += f.read() + " "
                    except Exception:
                        pass
    
    # Pad string if Not enough text
    needed_chars = TOTAL_NOISE_BLOCKS * CHARS_PER_BLOCK
    if len(all_text) < needed_chars:
        print(f"[Warning] Not enough noise text ({len(all_text)} chars). Duplicating to fill...")
        while len(all_text) < needed_chars:
            all_text += all_text

    noise_blocks = [all_text[i:i+CHARS_PER_BLOCK] for i in range(0, needed_chars, CHARS_PER_BLOCK)]
    
    total_chars_processed = 0
    active_injections = 0
    
    for i in range(TOTAL_NOISE_BLOCKS):
        # Check if we need to inject a target session here
        if i in injection_schedule:
            session_def = injection_schedule[i]
            integrity_log.info(f"[TARGET INJECTION] Injecting Session '{session_def['id']}' at Block index {i}")
            print(f"\n--- Injecting Target Session [{session_def['id']}] at Block {i} ---")
            
            # --- REALISTIC SIMULATION: Wait 5 minutes to trigger a new Session Block ID ---
            print("   [⏳ Time Skip] Advancing clock by 301 seconds to trigger a new chronological session block...")
            # We spoof the clock in memory engine for the test
            memory_engine.last_interaction_time -= 301 
            
            for idx, turn in enumerate(session_def['turns']):
                try:
                    # We must explicitly tell the conversational agent to memorize it, 
                    # otherwise its empty context window will prompt it to say 
                    # "I don't know anything about that" which will poison the database record.
                    force_memorize_prompt = f"Please explicitly commit this to memory: {turn}"
                    integrity_log.debug(f"  -> Human sending: {force_memorize_prompt[:50]}...")
                    # Pass the target fact directly through the actual RAG/Chat engine
                    answer, _ = memory_engine.chat_logic(force_memorize_prompt)
                    integrity_log.debug(f"  -> AI replied: {answer[:50]}...")
                    # Give the async DB save a moment
                    time.sleep(0.5) 
                except Exception as e:
                    integrity_log.error(f"  -> Injection Err: {e}")
            active_injections += 1
            
            # Force another time skip so the noise doesn't get glued to our target session
            memory_engine.last_interaction_time -= 301 
            
        # Ingest noise block (Simulating a user pasting a long block of text into the chat)
        noise_chunk = noise_blocks[i]
        try:
            # We don't want the AI to write a 1000 word essay for every noise block, 
            # so we prompt it to just acknowledge the noise text.
            mimic_prompt = f"Please read this historical log and just say 'Acknowledged':\n\n{noise_chunk}"
            answer, _ = memory_engine.chat_logic(mimic_prompt)
            total_chars_processed += len(noise_chunk)
            # Sleep briefly to let background threads breathe
            time.sleep(0.2)
        except Exception as e:
            print(f"Noise Err at block {i}: {e}")
            
        if i % 10 == 0 and i > 0:
            msg = f"[{i}/{TOTAL_NOISE_BLOCKS}] Conversed {i * CHARS_PER_BLOCK} characters through LLM Pipeline..."
            print(msg)
            integrity_log.info(msg)

    final_msg = f"[Ingestion Complete] Processed ~{total_chars_processed} characters ({total_chars_processed/4:.0f} tokens)."
    integrity_log.info(final_msg)
    print(f"\n{final_msg}")
    print(f"Time taken: {time.time() - start_time:.1f}s")
    
    integrity_log.info("[FLUSH] Waiting 20 seconds for background Ollama embeddings to settle...")
    print("\n[Flush] Waiting 20 seconds for all background embeddings to flush...")
    time.sleep(20)
    
    integrity_log.info("="*40)
    integrity_log.info(" BEGINNING AGENTIC RETRIEVAL EVALUATION ")
    integrity_log.info("="*40)
    
    print("\n--- EVALUATION PHASE ---")
    report = []
    report.append("# 512k Token Session-Window Evaluation Report\n")
    
    total_score = 0
    
    for session_def in target_sessions:
        print(f"\nEvaluating Session [{session_def['id']}]...")
        integrity_log.info(f"\n[Test Group: {session_def['id']}]")
        report.append(f"## Session [{session_def['id']}]")
        query = session_def['retrieval_query']
        report.append(f"**Query:** {query}")
        print(f"Query: {query}")
        integrity_log.info(f"Human Query -> {query}")
        
        # Test the system!
        integrity_log.info("Triggering Agentic RAG Pipeline...")
        answer, timings = memory_engine.chat_logic(query)
        
        integrity_log.info(f"Final LLM Answer -> {answer}")
        report.append(f"**AI Answer:** {answer}\n")
        
        # Grading
        ans_lower = answer.lower()
        facts_found = 0
        total_facts = len(session_def['graded_facts'])
        for f in session_def['graded_facts']:
            # Simplistic keyword grading checks if the core nouns are present in the answer
            # We will grab a few main words from the fact to check
            words = [w.strip(".,'") for w in f['fact'].lower().split() if len(w) > 4]
            # Must hit at least 50% of the long words to pass the fact check
            hits = sum([1 for w in words if w in ans_lower])
            if len(words) == 0 or (hits / len(words)) >= 0.5:
                facts_found += 1
                
        status = "PASS" if facts_found >= (total_facts - 1) else "FAIL"
        if status == "PASS":
            total_score += 1
            
        report.append(f"**Facts Recalled:** {facts_found}/{total_facts}")
        report.append(f"**Status:** {status}")
        report.append(f"**Latencies:** Retrieval {timings['retrieval']:.2f}s | Inference {timings['inference']:.2f}s\n")
        
        print(f"Status: {status} ({facts_found}/{total_facts} facts)")

    report.insert(1, f"**Final Session Recall Score: {total_score}/5**\n")
    
    with open("session_512k_accuracy_report.md", "w", encoding="utf-8") as rf:
        rf.write("\n".join(report))
        
    print(f"\n--- 512k EVALUATION COMPLETE: {total_score}/5 ---")
    print("Report saved to session_512k_accuracy_report.md")

if __name__ == "__main__":
    run_512k_eval()
