import requests, time

API_URL = "http://localhost:5000/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', 'your_key_here')}",
    "Content-Type": "application/json"
}
payload = {
    "model": "google/gemini-2.5-flash",
    "embed_model": "nvidia/llama-nemotron-embed-vl-1b-v2:free",
    "messages": [
        {"role": "user", "content": "What happens if we test a third model, like Gemini?"}
    ]
}

response = requests.post(API_URL, headers=headers, json=payload)
print(response.json())
