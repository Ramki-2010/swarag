"""Steps 3-4: Re-aggregate and update AGG paths."""
import os, subprocess, json

os.chdir(r"D:\Swaragam")

# Aggregate
print("[3] Aggregating...")
r = subprocess.run(
    [r"scripts\my_virtual_env_swarag\Scripts\python.exe", "scripts/aggregate_all_v12.py"],
    capture_output=True, text=True, cwd=r"D:\Swaragam"
)
print(r.stdout.strip())

# Find latest
agg_base = r"D:\Swaragam\pcd_results\aggregation\v1.2"
runs = sorted([d for d in os.listdir(agg_base) if d.startswith("run_")])
latest = os.path.join(agg_base, runs[-1])
print("Latest agg: " + latest)

# Update paths
for fname in ["scripts/batch_evaluate.py", "scripts/batch_evaluate_random.py"]:
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "AGG_FOLDER" in line and "=" in line and 'r"' in line:
            lines[i] = 'AGG_FOLDER   = r"' + latest + '"  # v1.3: 5 ragas, 55 clips\n'
            break
    with open(fname, "w", encoding="utf-8") as f:
        f.writelines(lines)
print("[4] AGG paths updated")
