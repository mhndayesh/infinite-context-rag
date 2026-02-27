import os
import glob
import random

input_dir = r'c:\new-ai,arch\archive\512k_window_evaluation\dataset512k'
output_path = r'c:\tmp\local_offline_memory\data\niah_test_512k.txt'

print(f'Reading files from {input_dir}')
files = glob.glob(os.path.join(input_dir, '*.txt'))

massive_text = ''
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            massive_text += file.read() + '\n\n'
    except Exception as e:
        print(f'Error reading {f}: {e}')

needle = "\n\n*** \nSUPER SECRET NEEDLE: The launch code for project Orion is 'Delta-Seven-Tango'. It was authorized by Commander Shepard on Stardate 4529.1 \n***\n\n"

# Insert at roughly 75% depth
insert_pos = int(len(massive_text) * 0.75)
final_text = massive_text[:insert_pos] + needle + massive_text[insert_pos:]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_text)

print(f'Generated: {output_path}')
print(f'Total Size: {len(final_text) / (1024*1024):.2f} MB')
print(f'Needle content: {needle.strip()}')
