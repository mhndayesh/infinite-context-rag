import json, os

def write_log(jsonl_path, out_path, model_name, run_date):
    if not os.path.exists(jsonl_path):
        print(f"Skipping: {jsonl_path} not found.")
        return
    with open(jsonl_path) as f:
        rows = [json.loads(l) for l in f if l.strip()]
    passed = sum(1 for r in rows if r['judge'])
    lines = []
    lines.append(f'{model_name.upper()} — RAW TEST LOG')
    lines.append('=' * 60)
    lines.append(f'Run date  : {run_date}')
    lines.append(f'Total     : {passed}/{len(rows)} PASSED ({int(passed/len(rows)*100)}%)')
    lines.append(f'Model     : {model_name}')
    lines.append(f'Embed     : nomic-embed-text')
    lines.append('')
    for r in rows:
        status = 'PASS' if r['judge'] else 'FAIL'
        depth_pct = int(r['depth'] * 100)
        ctx = r['context_length']
        lines.append(f"--- {r['test_id']} ---")
        lines.append(f"  Status     : {status}")
        lines.append(f"  Depth      : {depth_pct}% (needle at {depth_pct}% through document)")
        lines.append(f"  Context    : {ctx} tokens ({ctx*4} chars)")
        lines.append(f"  Embed time : {r.get('embed_time', 0):.2f}s")
        lines.append(f"  Retrieval  : {r['retrieval_time']:.3f}s  {'[FAST PATH]' if r['retrieval_time'] < 0.1 else '[LLM ROUTER]'}")
        lines.append(f"  Inference  : {r['inference_time']:.3f}s")
        lines.append(f"  Response   : {r['response']}")
        lines.append('')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Written: {out_path}')

# Use paths relative to this script's directory for reliability
script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, 'results')

write_log(
    os.path.join(results_dir, 'phi4-mini_3.8b_niah.jsonl'),
    os.path.join(results_dir, 'phi4-mini_RAW_LOG.txt'),
    'phi4-mini:3.8b',
    'February 24, 2026'
)

write_log(
    os.path.join(results_dir, 'dolphin-phi_2.7b_niah.jsonl'),
    os.path.join(results_dir, 'dolphin-phi_RAW_LOG.txt'),
    'dolphin-phi:2.7b',
    'February 23, 2026'
)

write_log(
    os.path.join(results_dir, 'deepseek-r1_8b_niah.jsonl'),
    os.path.join(results_dir, 'deepseek-r1_RAW_LOG.txt'),
    'deepseek-r1:8b',
    'February 24, 2026'
)
