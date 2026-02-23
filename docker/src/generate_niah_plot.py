import json
import os
import matplotlib.pyplot as plt
import numpy as np

def generate_plot():
    results_file = "results/dolphin-phi_2.7b_niah.jsonl"
    if not os.path.exists(results_file):
        print(f"File {results_file} not found. Run niah_eval.py first.")
        return

    data = []
    with open(results_file, 'r') as f:
         for line in f:
             data.append(json.loads(line))

    # Extract unique lengths and depths, preserving order
    lengths = sorted(list(set([item['context_length'] for item in data])))
    depths = sorted(list(set([item['depth'] for item in data])))

    # Create grid of shape [len(depths), len(lengths)]
    grid = np.zeros((len(depths), len(lengths)))

    for item in data:
        l_idx = lengths.index(item['context_length'])
        d_idx = depths.index(item['depth'])
        grid[d_idx, l_idx] = 1.0 if item['judge'] else 0.0

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Use a custom colormap (Red=Fail, Green=Pass)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(['#ff4b4b', '#00cc66'])

    cax = ax.matshow(grid, cmap=cmap, vmin=0, vmax=1)

    # Format Axes
    ax.set_xticks(np.arange(len(lengths)))
    ax.set_yticks(np.arange(len(depths)))
    ax.set_xticklabels([f"{int(l/1000)}k" for l in lengths])
    ax.set_yticklabels([f"{int(d*100)}%" for d in depths])

    ax.set_xlabel("Context Length (Tokens)")
    ax.set_ylabel("Document Depth (%)")
    ax.set_title("Needle In A Haystack (NIAH) Recall Grid", pad=20)

    # Add text annotations (optional, since it's just binary pass/fail)
    for i in range(len(depths)):
        for j in range(len(lengths)):
            text = "✅" if grid[i, j] == 1.0 else "❌"
            ax.text(j, i, text, ha="center", va="center", color="black", fontsize=14)

    plt.tight_layout()
    plt.savefig("results/niah_grid.png", dpi=300)
    print("Plot saved to results/niah_grid.png")

if __name__ == "__main__":
    generate_plot()
