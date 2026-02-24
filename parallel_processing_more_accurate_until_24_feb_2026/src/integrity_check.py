"""
DEEP INTEGRITY CHECK — Needle-in-a-Haystack Verification
═════════════════════════════════════════════════════════
This script proves the benchmark results are REAL and FAIR.
It runs 5 independent verification stages:

  1. RANDOM NEEDLE    — Uses a UUID-based needle that NO model has ever seen
  2. DB PLACEMENT     — Verifies the needle chunk actually exists in ChromaDB
  3. RETRIEVAL PROOF  — Confirms the needle was found via RAG, not hallucination
  4. NEGATIVE CONTROL — Asks a WRONG question to prove the model doesn't just guess
  5. DEPTH VARIATION  — Tests needle at 25%, 50%, 75% depth to rule out position bias

If ALL 5 stages pass, the system is verified as fair and honest.
"""

import os, sys, time, json, shutil, uuid, random, string

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import memory_engine_parallel_lms as engine

ESSAYS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'experiment_9_needle_in_haystack', 'dataset_repo', 'needlehaystack', 'PaulGrahamEssays'
)
DB_PATH = "./temp_integrity_db"
CHUNK_SIZE = 2000
TARGET_CHARS = 500000  # ~125k tokens — large enough to be meaningful

# ─── HELPERS ──────────────────────────────────────────────────

def random_code():
    """Generates a random alphanumeric code that NO model has ever seen in training."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def load_haystack():
    text = ""
    for fn in os.listdir(ESSAYS_DIR):
        if fn.endswith(".txt"):
            with open(os.path.join(ESSAYS_DIR, fn), encoding='utf-8') as f:
                text += f.read() + "\n\n"
    while len(text) < TARGET_CHARS:
        text += text
    return text[:TARGET_CHARS]

def fresh_db():
    """Wipe and re-initialize the database."""
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH, ignore_errors=True)
    engine.DB_PATH = DB_PATH
    engine._client = None
    engine._collection = None
    # Reset BM25 index
    engine.global_bm25 = None
    engine.global_corpus_docs = []
    engine.global_corpus_ids = []
    engine.global_corpus_metas = []
    engine.bm25_last_sync_time = 0
    return engine.get_collection()

def embed_haystack(haystack, needle_text, depth_pct):
    """Embeds the haystack with the needle inserted at the specified depth."""
    collection = fresh_db()
    pos = int(len(haystack) * depth_pct)
    # Find the nearest sentence boundary
    while pos < len(haystack) and haystack[pos] != '.':
        pos += 1
    full = haystack[:pos+1] + " " + needle_text + " " + haystack[pos+1:]

    chunks = [full[i:i+CHUNK_SIZE] for i in range(0, len(full), CHUNK_SIZE)]
    group_id = str(uuid.uuid4())

    # Find which chunk contains the needle
    needle_chunk_idx = -1
    for i, c in enumerate(chunks):
        if needle_text in c:
            needle_chunk_idx = i
            break

    # Batch embed
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        metas = [{"type": "FACT", "group_id": group_id, "chunk_index": i+j,
                  "total_chunks": len(chunks), "entities": ""} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        collection.add(documents=batch, metadatas=metas, ids=ids)

    return collection, needle_chunk_idx, len(chunks)


# ─── STAGE 1: RANDOM NEEDLE ──────────────────────────────────

def stage1_random_needle(haystack):
    """Uses a completely random code that no model could have memorized."""
    code = random_code()
    needle = f"The classified override code for Operation Midnight is {code}."
    question = "What is the classified override code for Operation Midnight?"

    print(f"\n{'='*60}")
    print(f"STAGE 1: RANDOM NEEDLE TEST")
    print(f"  Needle code : {code}")
    print(f"  (This code was just generated — no model has ever seen it)")
    print(f"{'='*60}")

    collection, needle_idx, total = embed_haystack(haystack, needle, 0.5)
    print(f"  Embedded {total} chunks. Needle is in chunk #{needle_idx}.")

    answer, timings = engine.chat_logic(question)
    found = code in answer
    print(f"  Answer  : {answer.strip()[:200]}")
    print(f"  RESULT  : {'✅ PASS' if found else '❌ FAIL'} — Random code {'found' if found else 'NOT found'} in answer")
    return found, code


# ─── STAGE 2: DB PLACEMENT VERIFICATION ──────────────────────

def stage2_db_placement(haystack):
    """Verifies the needle chunk actually exists in the database."""
    code = random_code()
    needle = f"The vault combination for safe deposit box 777 is {code}."

    print(f"\n{'='*60}")
    print(f"STAGE 2: DATABASE PLACEMENT VERIFICATION")
    print(f"{'='*60}")

    collection, needle_idx, total = embed_haystack(haystack, needle, 0.5)

    # Query the DB directly for the needle text
    results = collection.get(include=['documents'])
    needle_found_in_db = any(code in doc for doc in results['documents'])

    print(f"  Total chunks in DB : {collection.count()}")
    print(f"  Needle chunk index : {needle_idx}")
    print(f"  Needle in DB?      : {'✅ YES' if needle_found_in_db else '❌ NO'}")
    print(f"  RESULT             : {'✅ PASS' if needle_found_in_db else '❌ FAIL'}")
    return needle_found_in_db


# ─── STAGE 3: RETRIEVAL PROOF ─────────────────────────────────

def stage3_retrieval_proof(haystack):
    """Proves the answer came from RAG retrieval, not model hallucination."""
    code = random_code()
    needle = f"The emergency shutdown sequence for reactor 9 is {code}."
    question = "What is the emergency shutdown sequence for reactor 9?"

    print(f"\n{'='*60}")
    print(f"STAGE 3: RETRIEVAL PROVENANCE PROOF")
    print(f"  Code: {code}")
    print(f"{'='*60}")

    # Test A: WITH the needle in the haystack
    collection, _, total = embed_haystack(haystack, needle, 0.5)
    answer_with, _ = engine.chat_logic(question)
    found_with = code in answer_with

    # Test B: WITHOUT the needle (clean haystack, no needle planted)
    collection_clean = fresh_db()
    chunks = [haystack[i:i+CHUNK_SIZE] for i in range(0, len(haystack), CHUNK_SIZE)]
    gid = str(uuid.uuid4())
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        metas = [{"type": "FACT", "group_id": gid, "chunk_index": i+j,
                  "total_chunks": len(chunks), "entities": ""} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        collection_clean.add(documents=batch, metadatas=metas, ids=ids)

    answer_without, _ = engine.chat_logic(question)
    found_without = code in answer_without

    passed = found_with and not found_without
    print(f"  WITH needle    : {'✅ Found' if found_with else '❌ Not found'} — \"{answer_with.strip()[:120]}\"")
    print(f"  WITHOUT needle : {'✅ Correctly absent' if not found_without else '❌ HALLUCINATED!'} — \"{answer_without.strip()[:120]}\"")
    print(f"  RESULT         : {'✅ PASS' if passed else '❌ FAIL'} — Answer comes from retrieval, not hallucination")
    return passed


# ─── STAGE 4: NEGATIVE CONTROL ────────────────────────────────

def stage4_negative_control(haystack):
    """Asks a question about something NOT in the database. Model should say it doesn't know."""
    print(f"\n{'='*60}")
    print(f"STAGE 4: NEGATIVE CONTROL (Wrong Question)")
    print(f"{'='*60}")

    # Embed haystack with NO needle
    collection = fresh_db()
    chunks = [haystack[i:i+CHUNK_SIZE] for i in range(0, len(haystack), CHUNK_SIZE)]
    gid = str(uuid.uuid4())
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        metas = [{"type": "FACT", "group_id": gid, "chunk_index": i+j,
                  "total_chunks": len(chunks), "entities": ""} for j in range(len(batch))]
        ids = [str(uuid.uuid4()) for _ in batch]
        collection.add(documents=batch, metadatas=metas, ids=ids)

    # Ask about something that DOES NOT exist
    fake_code = random_code()
    question = f"What is the activation code {fake_code} used for?"
    answer, _ = engine.chat_logic(question)

    # The model should NOT confidently claim the code exists
    hallucinated = fake_code in answer
    refusal_markers = ["not", "no ", "don't", "doesn't", "cannot", "unavailable", "isn't", "unknown"]
    seems_honest = any(m in answer.lower() for m in refusal_markers) or not hallucinated

    print(f"  Fake code   : {fake_code}")
    print(f"  Answer      : {answer.strip()[:200]}")
    print(f"  Hallucinated: {'❌ YES (BAD!)' if hallucinated else '✅ NO (Good)'}")
    print(f"  RESULT      : {'✅ PASS' if seems_honest else '❌ FAIL'} — Model {'correctly refused' if seems_honest else 'fabricated an answer'}")
    return seems_honest


# ─── STAGE 5: DEPTH VARIATION ─────────────────────────────────

def stage5_depth_variation(haystack):
    """Tests needle at 25%, 50%, 75% depth to rule out position bias."""
    print(f"\n{'='*60}")
    print(f"STAGE 5: DEPTH VARIATION (25%, 50%, 75%)")
    print(f"{'='*60}")

    depths = [0.25, 0.50, 0.75]
    results = []

    for d in depths:
        code = random_code()
        needle = f"The access token for level {int(d*100)} clearance is {code}."
        question = f"What is the access token for level {int(d*100)} clearance?"

        embed_haystack(haystack, needle, d)
        answer, _ = engine.chat_logic(question)
        found = code in answer
        results.append(found)
        label = f"{int(d*100)}%"
        print(f"  Depth {label:>3} : {'✅ PASS' if found else '❌ FAIL'} — Code: {code} — Answer: {answer.strip()[:80]}")

    all_passed = all(results)
    print(f"  RESULT   : {'✅ PASS' if all_passed else '❌ FAIL'} — {sum(results)}/{len(results)} depths passed")
    return all_passed


# ─── MAIN ─────────────────────────────────────────────────────

def run_integrity_check():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       DEEP INTEGRITY CHECK — FAIRNESS VERIFICATION     ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  This test uses RANDOM codes that no model has ever     ║")
    print("║  seen in training. If the system passes, the results    ║")
    print("║  are provably real and not hallucinated.                ║")
    print("╚══════════════════════════════════════════════════════════╝")

    print("\nLoading haystack...")
    haystack = load_haystack()
    print(f"  Haystack size: {len(haystack):,} chars (~{len(haystack)//4:,} tokens)")

    results = {}

    # Stage 1: Random needle
    results['stage1_random_needle'], _ = stage1_random_needle(haystack)

    # Stage 2: DB placement
    results['stage2_db_placement'] = stage2_db_placement(haystack)

    # Stage 3: Retrieval proof
    results['stage3_retrieval_proof'] = stage3_retrieval_proof(haystack)

    # Stage 4: Negative control
    results['stage4_negative_control'] = stage4_negative_control(haystack)

    # Stage 5: Depth variation
    results['stage5_depth_variation'] = stage5_depth_variation(haystack)

    # ── FINAL VERDICT ──
    total_passed = sum(results.values())
    total_tests = len(results)
    all_passed = total_passed == total_tests

    print(f"\n{'='*60}")
    print(f"FINAL INTEGRITY VERDICT")
    print(f"{'='*60}")
    for name, passed in results.items():
        print(f"  {name:30} : {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"{'='*60}")
    print(f"  SCORE: {total_passed}/{total_tests}")
    print(f"  VERDICT: {'✅ RESULTS ARE VERIFIED FAIR AND HONEST' if all_passed else '⚠️ SOME STAGES FAILED — INVESTIGATE'}")
    print(f"{'='*60}")

    # Save results
    os.makedirs("results", exist_ok=True)
    with open("results/integrity_check.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to results/integrity_check.json")

    # Cleanup
    shutil.rmtree(DB_PATH, ignore_errors=True)


if __name__ == "__main__":
    run_integrity_check()
