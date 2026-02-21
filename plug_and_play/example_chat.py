"""
╔══════════════════════════════════════════════════════════════════╗
║  INTEGRATION EXAMPLES — How to use memory_engine.py             ║
║  in your own project, agent, or chatbot                          ║
╚══════════════════════════════════════════════════════════════════╝

Run this file directly to see all examples in action:
  python example_chat.py
"""

from memory_engine import chat_logic


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 1: Simplest possible usage
# Drop this into any script that needs persistent memory.
# ─────────────────────────────────────────────────────────────────

def example_1_simple():
    print("\n" + "="*50)
    print("EXAMPLE 1: Simple single call")
    print("="*50)

    # Tell the engine a fact
    answer1, _ = chat_logic("Please remember: my project budget is $120,000.")
    print(f"AI: {answer1}\n")

    # Ask about it later (even across sessions, even after restart)
    answer2, _ = chat_logic("What is my project budget?")
    print(f"AI: {answer2}\n")


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 2: Interactive loop  (for a simple chatbot UI)
# ─────────────────────────────────────────────────────────────────

def example_2_interactive_loop():
    print("\n" + "="*50)
    print("EXAMPLE 2: Interactive loop (Ctrl+C to stop)")
    print("="*50)

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nStopped.")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        answer, timings = chat_logic(user_input)
        print(f"AI: {answer}")
        print(f"   [{timings['retrieval']:.2f}s retrieval | {timings['inference']:.2f}s inference]\n")


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 3: Agent integration
# Wrap chat_logic as the memory module for any AI agent.
# ─────────────────────────────────────────────────────────────────

def example_3_agent_wrapper(agent_message: str) -> str:
    """
    Drop-in memory module for any agent.
    Your agent calls this instead of calling the LLM directly.
    The memory engine handles storage and retrieval automatically.

    Usage in your agent:
        from example_chat import memory_agent_turn
        response = memory_agent_turn("What did the user say about their deadline?")
    """
    answer, _ = chat_logic(agent_message)
    return answer


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 4: API endpoint wrapper (FastAPI / Flask style)
# Expose the memory engine as a REST endpoint.
# ─────────────────────────────────────────────────────────────────

def example_4_api_handler(request_body: dict) -> dict:
    """
    Wrap chat_logic for use in a FastAPI or Flask route.

    FastAPI example:
        @app.post("/chat")
        async def chat(body: dict):
            return api_chat_handler(body)

    Flask example:
        @app.route("/chat", methods=["POST"])
        def chat():
            return jsonify(api_chat_handler(request.json))
    """
    user_message = request_body.get("message", "")
    if not user_message:
        return {"error": "No message provided"}

    answer, timings = chat_logic(user_message)
    return {
        "answer": answer,
        "retrieval_seconds": round(timings["retrieval"], 3),
        "inference_seconds": round(timings["inference"], 3),
    }


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 5: Batch ingestion of documents
# Feed documents into memory before a chat session starts.
# ─────────────────────────────────────────────────────────────────

def example_5_batch_ingest(documents: list[str]):
    """
    Pre-load a list of documents into memory before starting a chat.
    Great for giving the agent context about a project, codebase, or spec.

    Usage:
        docs = [
            "Project Alpha budget: $500,000. Lead: Sarah Chen.",
            "Deadline: December 15, 2025. Stack: Python + FastAPI.",
            "The client is AcmeCorp. Primary contact: John Doe, john@acme.com"
        ]
        batch_ingest(docs)
        answer, _ = chat_logic("Who is the client for Project Alpha?")
    """
    print(f"\nIngesting {len(documents)} documents into memory...")
    for i, doc in enumerate(documents):
        prompt = f"Please explicitly commit this to memory: {doc}"
        answer, _ = chat_logic(prompt)
        print(f"  [{i+1}/{len(documents)}] Ingested: {doc[:60]}...")
    print("Ingestion complete. Memory is ready.\n")


# ─────────────────────────────────────────────────────────────────
# MAIN — runs all examples when executed directly
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nChoose an example to run:")
    print("  1 - Simple single call (store + recall a fact)")
    print("  2 - Interactive chat loop")
    print("  3 - Agent wrapper demo")
    print("  4 - API handler demo")
    print("  5 - Batch document ingestion")
    print("  q - Quit")

    choice = input("\nEnter choice: ").strip()

    if choice == "1":
        example_1_simple()
    elif choice == "2":
        example_2_interactive_loop()
    elif choice == "3":
        test_msg = "What was the last thing I told you?"
        result = example_3_agent_wrapper(test_msg)
        print(f"\nAgent wrapper result:\nQ: {test_msg}\nA: {result}")
    elif choice == "4":
        test_request = {"message": "What projects are we working on?"}
        result = example_4_api_handler(test_request)
        print(f"\nAPI handler result:\n{result}")
    elif choice == "5":
        sample_docs = [
            "Project Vanguard lead is Dr. Elena Rostova. Budget: 850 million euros.",
            "The submersible is named Leviathan. Deployment date: October 4th.",
            "Operation base: Pacific Ocean. Mission: deep-sea geothermal tapping."
        ]
        example_5_batch_ingest(sample_docs)
        answer, _ = chat_logic("Who leads Project Vanguard and what is the budget?")
        print(f"\nRecall test:\nQ: Who leads Project Vanguard and what is the budget?\nA: {answer}")
    else:
        print("No example selected.")
