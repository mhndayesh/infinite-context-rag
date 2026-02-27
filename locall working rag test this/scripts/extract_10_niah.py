import random
import re

file_path = r'c:\tmp\niah_test_512k.txt'

print(f'\n--- Generating 10 Questions from {file_path} ---\n')

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read the massive file
        content = f.read()
        
        # Split roughly into 10 partitions so we get questions spread throughout the entire 116MB
        partition_size = len(content) // 10
        
        for i in range(10):
            start = i * partition_size
            end = (i + 1) * partition_size
            
            # Pick a random 2000 character chunk within this 10% partition
            chunk_start = random.randint(start, end - 2000)
            chunk = content[chunk_start:chunk_start + 2000]
            
            # Find a complete sentence that looks like a concrete fact (contains capitalized words, numbers, etc)
            sentences = re.split(r'(?<=[.!?]) +', chunk)
            
            # Filter for decent length sentences
            valid_sentences = [s for s in sentences if 40 < len(s) < 200 and ('\n' not in s)]
            
            if valid_sentences:
                fact = random.choice(valid_sentences)
                print(f"Fact {i+1} (Depth: ~{(chunk_start/len(content))*100:.1f}%):")
                print(f"[{fact.strip()}]\n")
            else:
                 print(f"Fact {i+1} (Depth: ~{(chunk_start/len(content))*100:.1f}%):")
                 print(f"[{sentences[len(sentences)//2].strip()}]\n")

except Exception as e:
    print(f'Error: {e}')
