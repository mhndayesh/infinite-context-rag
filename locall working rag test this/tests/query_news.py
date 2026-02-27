import memory_engine_parallel_lms as engine
import sys

def interactive_news_test():
    print("--- News Dataset Natural Recall Test ---")
    print("Ask a question about the news (e.g., 'What was the situation in US reports?')")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        print("\n🤔 Assistant is thinking...")
        answer, timings = engine.chat_logic(user_input)
        
        print(f"\n🤖 Assistant: {answer}")
        print(f"\n[Timings: {timings}]\n")

if __name__ == "__main__":
    interactive_news_test()
