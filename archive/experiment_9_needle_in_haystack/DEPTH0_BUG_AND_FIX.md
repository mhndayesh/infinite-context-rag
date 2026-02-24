# Bug Report: Depth-0 Retrieval Failure

**Date:** February 24, 2026
**Symptom:** NIAH tests with the needle at depth 0% (start of document) fail at all
context lengths above 8k, even though the keyword pre-filter correctly finds the
right chunk.

---

## The Problem, Simply

Imagine a library book. The answer you need is on **page 1**. The librarian finds
page 1 correctly, but then hands you: page 1 + pages 2 through 50 (random unrelated
text). By the time the AI reads to page 50 it has mentally "moved on" from page 1,
and guesses the wrong answer.

There are **two compounding bugs**:

### Bug 1 — No Left Context (Empty Window)

When the needle chunk is at position 0 in the document, Stage 3 tries to expand a
context window around it:

```
  [LEFT expansion]  → chunk_index = -1  → NOTHING (start of document)
  [RIGHT expansion] → chunks 1, 2, 3... → wall of unrelated essay text
```

Result: The needle (80 chars) gets buried under 5,920 chars of irrelevant text.

### Bug 2 — LLM Primacy Bias

Large Language Models pay **much more attention to text at the top of their
context window** than text in the middle. When the needle is buried after 3,000
chars of Paul Graham text, the LLM pattern-matches on the few-shot template in
the messages and hallucinates a password like `HAYSTICK-DELTA-9` instead of
reading the actual needle.

---

## Evidence

All depth_0 failures output the same hallucination pattern:
- `"PASSWORD FOR CORE MAINFRAME BENCHMARK TEST: HAYSTICK-DELTA-9"` at 128k-512k depth_0

This is NOT a retrieval failure (retrieval times: 0.036-0.047s = keyword fast-path
fired correctly). The **needle was found**, but the LLM ignored it.

---

## The Fix (Two Parts)

### Fix 1 — Right-Side Bias When Left Context Is Empty

In `memory_engine.py`, Stage 3 context exhumation now detects when `center_idx == 0`
(needle at document start) and uses the full context budget for RIGHT expansion only,
rather than splitting it 50/50 left/right.

**Before:** 3,000 chars left | needle (80) | 3,000 chars right
**After:**  needle (80) | 6,000 chars right (no left dead space)

### Fix 2 — Pin the Keyword-Winner Chunk First in the Prompt

When the keyword pre-filter fires and selects a specific chunk, that chunk is now
**prepended to the front of the `past_memory` context** before the rest of the
exhumed window. This exploits LLM primacy bias in our favor: the most relevant
80-char needle sentence is the FIRST thing the AI reads.

**Before:** [random essay...] ... [needle in middle] ... [more essay...]
**After:**  [needle FIRST] ... [surrounding context below] ...

---

## Expected Impact

These fixes target all 5 depth_0 failures (32k, 128k, 256k, 512k). Combined with the
existing anti-refusal and keyword pre-filter fixes, the target score is **23/25+**.
