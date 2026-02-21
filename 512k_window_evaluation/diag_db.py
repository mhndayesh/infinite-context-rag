import memory_engine
collection = memory_engine.get_collection()
results = collection.query(query_texts=["Project Vanguard"], n_results=10)
print("Hits for 'Project Vanguard':")
for i, doc in enumerate(results['documents'][0]):
    print(f"[{i}]: {doc[:200]}...")
    print(f"Meta: {results['metadatas'][0][i]}")
