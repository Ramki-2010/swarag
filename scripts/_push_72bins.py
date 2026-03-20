"""Push 72 bins to production scripts."""
import os, re, glob

os.chdir(os.path.dirname(__file__))

# 1. Update N_BINS in recognize_raga_v12.py
with open('recognize_raga_v12.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    'N_BINS           = 36   # Must match aggregation bins',
    'N_BINS           = 72   # Phase 4: was 36 (finer microtonal resolution)')
with open('recognize_raga_v12.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('OK: recognize_raga_v12.py N_BINS=72')

# 2. Update N_BINS in aggregate_all_v12.py
with open('aggregate_all_v12.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('N_BINS = 36', 'N_BINS = 72  # Phase 4: was 36')
with open('aggregate_all_v12.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('OK: aggregate_all_v12.py N_BINS=72')

# 3. Find latest 72-bin aggregation folder
agg_dirs = glob.glob(r'D:\Swaragam\pcd_results\aggregation\v1.2\run_*_72bins')
if not agg_dirs:
    print('ERROR: No 72-bin aggregation folder found')
else:
    latest_72 = sorted(agg_dirs)[-1]
    
    # Update batch_evaluate.py
    with open('batch_evaluate.py', 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(
        r'AGG_FOLDER\s+=\s+r"[^"]*"',
        'AGG_FOLDER   = r"' + latest_72 + '"',
        content)
    with open('batch_evaluate.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: batch_evaluate.py -> ' + os.path.basename(latest_72))
    
    # Update batch_evaluate_random.py
    with open('batch_evaluate_random.py', 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(
        r'AGG_FOLDER\s+=\s+r"[^"]*"',
        'AGG_FOLDER   = r"' + latest_72 + '"',
        content)
    with open('batch_evaluate_random.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: batch_evaluate_random.py -> ' + os.path.basename(latest_72))

# Verify
print()
print('=== VERIFICATION ===')
for f in ['recognize_raga_v12.py', 'aggregate_all_v12.py']:
    with open(f, 'r', encoding='utf-8') as fh:
        for line in fh:
            if 'N_BINS' in line and '72' in line:
                print('  ' + f + ': ' + line.strip())
                break

for f in ['batch_evaluate.py', 'batch_evaluate_random.py']:
    with open(f, 'r', encoding='utf-8') as fh:
        for line in fh:
            if 'AGG_FOLDER' in line and '=' in line and 'r"' in line:
                print('  ' + f + ': ' + line.strip())
                break
