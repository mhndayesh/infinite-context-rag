import random
import re

file_path = r'c:\tmp\local_offline_memory\data\niah_test_512k.txt'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read the massive file
        content = f.read()
        
        # Split roughly into 10 partitions so we get questions spread throughout the entire 116MB
        partition_size = len(content) // 10
        
        print('\n--- Generate 10 Questions from ' + file_path + ' ---\n')
        
        for i in range(10):
            start = i * partition_size
            end = (i + 1) * partition_size
            
            # Pick a random 2000 character chunk within this 10% partition
            chunk_start = random.randint(start, end - 2000)
            chunk = content[chunk_start:chunk_start + 2000]
            
            # Find a complete sentence that looks like a concrete fact (contains capitalized words, numbers, etc)
            sentences = re.split(r'(?<=[.!?]) +', chunk)
            
            # Filter for decent length sentences avoiding HTML tags
            valid_sentences = [s for s in sentences if 40 < len(s) < 200 and ('\n' not in s) and ('<' not in s)]
            
            if valid_sentences:
                fact = valid_sentences[len(valid_sentences)//2]
                print(f"Location: ~{(chunk_start/len(content))*100:.1f}% Depth")
                print(f"Raw Text: {fact.strip()}\n")

except Exception as e:
    print(f'Error: {e}')
