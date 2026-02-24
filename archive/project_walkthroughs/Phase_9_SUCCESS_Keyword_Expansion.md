# Walkthrough: Phase IX (SUCCESS: Agentic Query Expansion)

## Overview
Phase VIII gave us the ability to retrieve an entire conversational block perfectly... *if* the Vector DB found a hit inside that block. However, against 128,000 characters of noise, casual human queries (e.g., "What was the Jira ticket for our caching issue?") suffered from **Semantic Dilution**. Dense IT news articles about "servers" and "issues" outranked the specific conversation, meaning our target block didn't even make it into the Top 10 hits to be processed by our Stage 2 Router.

## The Final Architecture (What We Built)

We deployed a **Pre-Search Agentic Router**. We realized that LLMs are vastly superior to humans at formulating search strings for Vector Databases. 

1. **The Interception:** When a user asks a casual question, instead of querying ChromaDB immediately, the script halts.
2. **The Extraction Phase (`extract_keywords`):** A fast LLM (`llama3.2:3b`) receives a hidden system prompt. It reads the user's casual question, strips away all grammar and conversational fluff, and outputs a highly dense, comma-separated keyword payload (e.g., `Jira, ticket, caching, issue, Redis, permanent solution`).
3. **The Laser-Guided Search:** The script feeds this dense payload into ChromaDB's Stage 1 query. 

## The Results (Victory)

We re-ran the massive 32k Token Session-Window evaluation. We buried 5 specific chat sessions inside 128,000 characters of dense news articles. 

- **Score:** The keyword expansion payload acted like a laser beam, instantly piercing the 128k noise floor. 
- **Retrieval:** It forced all 5 Target Sessions into the Top 10 Stage 1 hits. 
- **The Agentic Exhumation:** Stage 2 correctly identified the center-point index, and Stage 3 successfully pulled the *entire surrounding conversation blocks* for all 5 topics.
- **Accuracy:** The system achieved a perfect 5/5 retrieval score, completely solving the "Semantic Dilution" problem. It successfully recalled specific nested facts deep from within 128,000 characters of history, *despite the inference model (`llama3.2:3b`) being hard-locked to a strict 4,000 token Context Window to run on consumer hardware.*

***

**Final Architecture Pipeline:**
`Casual Human Query -> LLM Keyword Expander -> Stage 1 Vector Hit -> Stage 2 LLM Router -> Stage 3 Session Block Exhumation -> Final 4k LLM Context Window`
