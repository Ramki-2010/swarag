"""Update AGG paths + run LOO validation on 9 ragas."""
import os

new_agg = r'D:\Swaragam\pcd_results\aggregation\v1.2\run_20260320_041912'

for fname in ['batch_evaluate.py', 'batch_evaluate_random.py']:
    with open(fname, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 'AGG_FOLDER' in line and '=' in line:
            if 'r"' in line:
                lines[i] = 'AGG_FOLDER   = r"' + new_agg + '"  # 9 ragas, 81 clips, 72 bins\n'
                print('Updated: ' + fname)
                break
    with open(fname, 'w', encoding='utf-8') as f:
        f.writelines(lines)

print('Done')
