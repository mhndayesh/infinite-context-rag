import os
import glob
import random

input_dir = r'c:\new-ai,arch\archive\512k_window_evaluation\dataset512k'
files = glob.glob(os.path.join(input_dir, '*.txt'))

# Select 10 random files to pull facts from
random.seed(42)  # For reproducibility
selected_files = random.sample(files, 10)

print(f'Extracting 10 random facts from the dataset...\n')

for i, f in enumerate(selected_files, 1):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            text = file.read()
            
            # Pick a random 500-character snippet from somewhere in the middle of the file
            start_pos = random.randint(len(text)//4, (len(text)//4)*3)
            snippet = text[start_pos:start_pos+1000]
            
            # Try to grab a sentence or two
            sentences = snippet.split('. ')
            if len(sentences) > 2:
                fact = sentences[1].strip() + '.'
            else:
                fact = snippet.strip()[:150] + '...'
                
            print(f'--- Fact {i} (from {os.path.basename(f)} @ {start_pos}) ---')
            print(f'{fact}\n')
            
    except Exception as e:
        print(f'Error reading {f}: {e}')
