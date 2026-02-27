import requests
import json
import time
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

API_URL = "http://localhost:5000/v1/chat/completions"

def test_chat():
    print("🚀 Testing Local API with .env configuration...")
    
    # 1. Grab keys from dotenv
    api_key = os.getenv("OPENROUTER_API_KEY")
    llm_model = os.getenv("TEST_USER_LLM")
    embed_model = os.getenv("TEST_USER_EMBED")
    
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in .env")
        return

    # 2. Add BYOK to Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 3. Add Custom Models to Payload
    payload = {
        "model": llm_model,
        "embed_model": embed_model,
        "messages": [
            {"role": "user", "content": "Tell me about the Australian cricket milestone with Nathan Lyon."}
        ],
        "temperature": 0.0
    }
    
    print(f"👉 Sending Payload:")
    print(f"   - LLM: {llm_model}")
    print(f"   - Embeddings: {embed_model}")
    
    try:
        start = time.perf_counter()
        response = requests.post(API_URL, headers=headers, json=payload)
        elapsed = time.perf_counter() - start
        
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            print(f"\n✅ SUCCESS (Time: {elapsed:.2f}s)")
            print(f"AI Answer: {answer[:300]}...")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_chat()
