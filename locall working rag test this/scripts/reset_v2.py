import memory_engine_parallel_lms as engine
try:
    print("Resetting Collection 'news_memory_v2'...")
    engine.chroma_client.delete_collection("news_memory_v2")
    engine.get_collection() # Recreate it
    print("Success! Collection is now empty.")
except Exception as e:
    print("❌ Reset Error:", e)
