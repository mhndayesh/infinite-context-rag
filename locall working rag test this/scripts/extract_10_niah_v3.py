import random
import re

file_path = r'c:\tmp\niah_test_512k.txt'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        partition_size = len(content) // 10
        
        for i in range(10):
            start = i * partition_size
            end = (i + 1) * partition_size
            
            chunk_start = random.randint(start, end - 2000)
            chunk = content[chunk_start:chunk_start + 2000]
            
            sentences = re.split(r'(?<=[.!?]) +', chunk)
            valid_sentences = [s for s in sentences if 40 < len(s) < 200 and ('\n' not in s) and ('<' not in s)]
            
            if valid_sentences:
                fact = valid_sentences[len(valid_sentences)//2]
                print(f"Location: ~{(chunk_start/len(content))*100:.1f}% Depth")
                print(f"Raw Text: {fact.strip()}\n")

except Exception as e:
    print(f'Error: {e}')
