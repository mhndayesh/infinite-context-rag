import memory_engine_parallel_lms as engine
try:
    print("Attempting to connect to ChromaDB Server (v2) via engine...")
    collection = engine.get_collection()
    print("Success! Collection name:", collection.name)
    print("Current Count:", collection.count())
except Exception as e:
    print("❌ Engine Connection Error:", e)
    import traceback
    traceback.print_exc()
