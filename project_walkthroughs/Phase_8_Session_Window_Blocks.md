# Walkthrough: Phase VIII (Session-Window Block Retrieval)

## Overview
While Phase VII successfully pulled full *documents*, natural human conversation doesn't happen in single documents. It happens in back-and-forth turns over time. We needed a way to pull an entire conversation history at once.

## What We Built
1. **Time-Based Clustering:** We introduced a global `session_block_id` governed by an `IDLE_TIMEOUT` of 5 minutes. 
2. **The Mathematical Stapler:** As long as a user keeps chatting, every single back-and-forth message is stapled together with the same invisible `session_block_id` and assigned a chronological `chunk_index`.
3. **Integration with Two-Stage RAG:** We wired this into the Stage 3 exhumation engine. Now, if the AI routed to a single sentence about a "Space Pirate," it wouldn't just grab that sentence. It would mathematically yank the *entire 5-minute conversation* surrounding that pirate out of the database.

## The Results
During a simulated test, the AI successfully reconstructed an entire complex narrative (Character names, ship names, weapons) just by landing a single vector hit on the timeline. It perfectly parsed the chronology and ignored irrelevant chats from other blocks.

**The Remaining Flaw:** While Stage 3 Exhumation was perfect, Stage 1 Vector retrieval still occasionally failed to put the target conversation into the "Top 10" hits when buried under massive amounts of noise.
