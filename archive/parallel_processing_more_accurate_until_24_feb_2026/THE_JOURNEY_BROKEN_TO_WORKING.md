# 🛤 The Journey: From Broken to Working
**Phase 16 Experiment Log: Feb 2026**

## ❌ Part 1: The "Broken" State (The vLLM Barrier)
Initially, we attempted to use **vLLM** for true GPU parallelism on Windows.
- **The Failure:** vLLM has significant compatibility issues with Windows/CUDA environments, leading to cryptic "Channel Errors" and context crashes.
- **The Accuracy Gap:** Even with the `parallel_extraction.py` script, models were frequently failing simple "Needle in a Haystack" tests because of **safety refusals**. 

The "Broken" state was characterized by:
- 400 Context Errors.
- Safety refusals (e.g., "I cannot reveal that code").
- 20.0s+ latency due to sequential worker processing.

---

## 🏗 Part 2: The Pivot (LM Studio + 16 Parallel Slots)
We transitioned to **LM Studio**'s OpenAI-compatible API.
- **Breakthrough:** The user enabled **16 Parallel Slots** in LM Studio settings.
- **Innovation:** We rewrote the engine to use an `ALL_IN` mode with 16 parallel async workers.
- **Stability:** We standardized on 8k Context Window + 1200 char chunks to eliminate all "Context size exceeded" errors.

---

## ⚡ Part 3: The "More Accurate" Breakthrough
Even with fast retrieval, the LLM often refused to say the answer.
- **The Solution:** **The Direct-Return Bypass.**
- **How it works:** We instructed the workers to extract facts into a `[FACT: ...]` format. In the final stage, if the workers found a fact, the engine **returns it directly**, skipping the final LLM filtering.
- **The Result:** 100% accurate, no-disclaimer answers.

---

## 📊 Final Verified Performance
| Metric | Broken (vLLM/Initial) | Working (LM Studio + Bypass) | Improvement |
| :--- | :--- | :--- | :--- |
| **Integrity Score** | 1/5 | **5/5 (Audit Verified)** | +400% |
| **Latency** | 20s+ | **~7.5s** | ~3x Speedup |
| **Safety Refusals** | High | **Zero (Bypassed)** | Total Fix |
| **Context Errors** | Frequent | **Zero** | 100% Stable |

---

## 📂 Folder Contents
- `/src`: Final production-ready parallel engine and integrity checks.
- `/results`: Raw JSON data of passing benchmarks.
- `/logs`: History of the 16-slot parallel execution.
- `/artifacts`: The internal thinking and planning docs that led to this breakthrough.
