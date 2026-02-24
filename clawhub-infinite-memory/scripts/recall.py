import sys
import requests
import json

def recall(query):
    url = "http://127.0.0.1:8000/search"
    headers = {"X-API-Key": "oc-memory-secret-123"}
    try:
        response = requests.post(url, json={"query": query}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"[RECALLED FACT]: {data['answer']}")
        elif response.status_code == 403:
            print("Error: Authentication failed. Invalid API Key.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: Could not connect to Memory Service. Is it running? {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recall.py \"your query\"")
    else:
        recall(sys.argv[1])
