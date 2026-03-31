"""Update AGG paths to 7-raga model."""
new_agg = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260331_232228"
for fname in ["batch_evaluate.py", "batch_evaluate_random.py"]:
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "AGG_FOLDER" in line and "=" in line and 'r"' in line:
            lines[i] = 'AGG_FOLDER   = r"' + new_agg + '"  # v1.3.1: 7 ragas, 70 clips\n'
            break
    with open(fname, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Updated: " + fname)
