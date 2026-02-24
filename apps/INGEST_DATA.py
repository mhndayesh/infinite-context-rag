"""
📂 Infinite Context RAG — DATA INGESTOR
═══════════════════════════════════════
Drop your text files (.txt) into the 'source_docs' folder,
then run this script to add them to your knowledge base.
"""

import os
import uuid
import sys

# Ensure we can import the engine config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import memory_engine_parallel_lms as engine

DATA_FOLDER = "source_docs"
CHUNK_SIZE = 1000  # Size of each piece of text in characters

def ingest_data():
    collection = engine.get_collection()
    
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        print(f"\n[!] Created '{DATA_FOLDER}' folder.")
        print(f"    Drop your .txt files there and run this script again.")
        return

    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.txt')]
    
    if not files:
        print(f"\n[!] No .txt files found in '{DATA_FOLDER}'.")
        print(f"    Add some files and try again.")
        return

    print(f"\n🚀 Found {len(files)} files. Starting ingestion...")
    
    for filename in files:
        filepath = os.path.join(DATA_FOLDER, filename)
        print(f"   📄 Processing: {filename}...")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            
        # Basic chunking
        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        
        # Prepare batches for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({"source": filename, "chunk": idx})
            ids.append(str(uuid.uuid4()))
            
            # Add in batches of 50 to avoid any payload limits
            if len(documents) >= 50:
                collection.add(documents=documents, metadatas=metadatas, ids=ids)
                documents, metadatas, ids = [], [], []

        # Add remaining
        if documents:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            
        print(f"   ✅ Done! Added {len(chunks)} chunks from {filename}.")

    print(f"\n✨ SUCCESS: Your database now contains {collection.count()} total items.")
    print(f"   You can now run 'QUICK_START_CHAT.py' to ask questions about this data.")

if __name__ == "__main__":
    ingest_data()
