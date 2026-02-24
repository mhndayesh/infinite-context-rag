import sys
import requests
import json

def ingest(filename, text):
    url = "http://127.0.0.1:8000/ingest"
    headers = {"X-API-Key": "oc-memory-secret-123"}
    try:
        response = requests.post(url, json={"filename": filename, "text": text}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Success: Stored {data['chunks_added']} chunks to memory.")
        elif response.status_code == 403:
            print("Error: Authentication failed. Invalid API Key.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: Could not connect to Memory Service. Is it running? {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ingest.py \"filename\" \"text content\"")
    else:
        ingest(sys.argv[1], sys.argv[2])
