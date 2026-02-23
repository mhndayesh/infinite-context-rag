import urllib.request
import json
import time

def check_models():
    req = urllib.request.Request('http://localhost:11434/api/ps')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("\n--- Current Loaded Models in Ollama ---")
            for model in data.get('models', []):
                name = model.get('name', 'Unknown')
                total_gb = model.get('size', 0) / (1024**3)
                vram_gb = model.get('size_vram', 0) / (1024**3)
                ram_gb = total_gb - vram_gb
                print(f"[{name}] Total: {total_gb:.2f} GB | In VRAM: {vram_gb:.2f} GB | In CPU RAM: {ram_gb:.2f} GB")
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")

if __name__ == '__main__':
    check_models()
