import memory_engine_parallel_lms as engine
import json

def inspect_db():
    print("--- ChromaDB Collection Inspection ---")
    try:
        collection = engine.get_collection()
        print(f"Total items in collection: {collection.count()}")
        
        # Get the 5 most recent items
        results = collection.get(limit=5, include=['documents', 'metadatas'])
        
        print("\nLast 5 items:")
        for idx in range(len(results['ids'])):
            print(f"\nID: {results['ids'][idx]}")
            print(f"Metadata: {results['metadatas'][idx]}")
            print(f"Document: {results['documents'][idx][:200]}...")
            
    except Exception as e:
        print(f"Error inspecting DB: {e}")

if __name__ == "__main__":
    inspect_db()
