"""Fix batch evaluate AGG paths to 72-bin models."""
import os, glob

os.chdir(os.path.dirname(__file__))

agg_dirs = glob.glob(r'D:\Swaragam\pcd_results\aggregation\v1.2\run_*_72bins')
if not agg_dirs:
    print('ERROR: No 72-bin folder found')
    exit(1)

latest_72 = sorted(agg_dirs)[-1]
print('72-bin folder: ' + latest_72)

for fname in ['batch_evaluate.py', 'batch_evaluate_random.py']:
    with open(fname, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if 'AGG_FOLDER' in line and '=' in line:
            if 'r"' in line or "r'" in line:
                lines[i] = 'AGG_FOLDER   = r"' + latest_72 + '"  # Phase 4: 72 bins\n'
                print('  Updated: ' + fname)
                break
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# Verify all 4 files
print('')
print('=== FINAL VERIFICATION ===')
checks = [
    ('recognize_raga_v12.py', 'N_BINS'),
    ('aggregate_all_v12.py', 'N_BINS'),
    ('batch_evaluate.py', 'AGG_FOLDER'),
    ('batch_evaluate_random.py', 'AGG_FOLDER'),
]
for fname, key in checks:
    with open(fname, 'r', encoding='utf-8') as f:
        for line in f:
            if key in line and '72' in line:
                print('  OK ' + fname + ': ' + line.strip())
                break
