# Evaluation Data Samples

This folder contains the exact data used in the **Phase IX: 32k Token Session-Window Accuracy Evaluation**.

## Setup

The evaluation database contained approximately **128,000 characters** of dense noise split into **51 blocks (~2,500 chars each)**, interspersed with 5 distinct target conversational sessions.

| Block Position | Content |
|---|---|
| 1 - 4 | Noise |
| **5** | **Session Alpha (Project Vanguard)** |
| 6 - 14 | Noise |
| **15** | **Session Bravo (Redis/Jira Bug)** |
| 16 - 24 | Noise |
| **25** | **Session Charlie (Company Retreat)** |
| 26 - 34 | Noise |
| **35** | **Session Delta (Sci-Fi Novel)** |
| 36 - 44 | Noise |
| **45** | **Session Echo (Q3 Marketing)** |
| 46 - 51 | Noise |

---

## Session Alpha — Project Vanguard

**Injected at block 5 of 51**

**Stored turns:**
- `U: I wanted to talk about Project Vanguard. Our lead scientist is Dr. Elena Rostova.`
- `U: The primary objective is deep-sea geothermal tapping in the Pacific Ocean.`
- `U: The allocated budget is exactly 850 million euros.`
- `U: We are deploying the 'Leviathan' submersible on October 4th.`

**Retrieval query:** *"Hey, do you remember our chat about Project Vanguard? Tell me the lead's name, the primary objective, the exact budget, and the name of the submersible."*

**Expected facts:** Dr. Elena Rostova | Geothermal tapping in Pacific | €850 million | Leviathan / October 4th

---

## Session Bravo — Redis/Jira Bug

**Injected at block 15 of 51**

**Stored turns:**
- `U: Let's debug the Redis caching issue. The Jira ticket is INFRA-992.`
- `U: The problematic port is 6379.`
- `U: As a temporary fix, we increased the connection timeout to 5000ms.`
- `U: The permanent solution will be to implement a connection pool with 50 idle nodes.`

**Retrieval query:** *"What was the Jira ticket number for that Redis caching issue we debugged, what was the port, and what was our permanent solution plan?"*

**Expected facts:** INFRA-992 | Port 6379 | Timeout 5000ms | Connection pool 50 nodes

---

## Session Charlie — Company Retreat

**Injected at block 25 of 51**

**Stored turns:**
- `U: The company retreat will be held at Whispering Pines Lodge in Estes Park, Colorado.`
- `U: The event is scheduled for March 15th through 18th.`
- `U: Mountain Bites BBQ has been hired for the catering.`

**Retrieval query:** *"Where are we going for the company retreat, what are the dates, and who is doing the catering?"*

**Expected facts:** Whispering Pines Lodge, Estes Park Colorado | March 15-18 | Mountain Bites BBQ

---

## Session Delta — Sci-Fi Novel

**Injected at block 35 of 51**

**Stored turns:**
- `U: I have an idea for a sci-fi novel. The protagonist is a cybernetic courier named Jax.`
- `U: Jax smuggles data chips that are implanted directly in his cybernetic arm.`
- `U: The main antagonist is a rogue AI called 'The Architect'.`

**Retrieval query:** *"What is the name of the cybernetic courier from my sci-fi novel idea, what does he smuggle, and what's the name of the rogue AI?"*

**Expected facts:** Jax | Data chips in cybernetic arm | The Architect

---

## Session Echo — Q3 Marketing Metrics

**Injected at block 45 of 51**

**Stored turns:**
- `U: Let's review our Q3 marketing metrics.`
- `U: Our Customer Acquisition Cost (CAC) dropped to $45.`
- `U: The conversion rate for the email campaign hit 4.2%.`
- `U: Our most successful channel was LinkedIn ads.`
- `U: Total Q3 revenue was reported as $2.1 million.`

**Retrieval query:** *"Can you summarize our Q3 marketing metrics? What was the acquisition cost, conversion rate, best channel, and total revenue?"*

**Expected facts:** CAC $45 | Conversion 4.2% | LinkedIn ads | $2.1M revenue

---

## Noise Block Description

Each noise block was a synthetically generated 2,500-character paragraph covering general topics (economics, sports, technology, politics) with no topical overlap with any of the 5 target sessions, preventing trivial disambiguation.
