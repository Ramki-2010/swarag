"""Patch batch_evaluate.py: add per-file timeout + progress counter + elapsed time."""

with open("batch_evaluate.py", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Add imports
old_imports = 'import os\r\nimport csv\r\nimport numpy as np'
new_imports = 'import os\r\nimport csv\r\nimport time\r\nimport numpy as np\r\nfrom concurrent.futures import ThreadPoolExecutor, TimeoutError'
c = c.replace(old_imports, new_imports)

# 2. Add timeout constant
c = c.replace(
    'SUPPORTED_EXTS = (".wav", ".mp3", ".flac")',
    'SUPPORTED_EXTS = (".wav", ".mp3", ".flac")\r\nPER_FILE_TIMEOUT = 360  # 6-minute timeout per file'
)

# 3. Wrap recognize_raga call with timeout + timer
old_call = '''            total_files += 1
            audio_path  = os.path.join(raga_path, file)

            # C2: use v1.2 API \u2014 (audio_path, aggregation_folder, models)
            result = recognize_raga(audio_path, AGG_FOLDER, models=models)'''

new_call = '''            total_files += 1
            audio_path  = os.path.join(raga_path, file)
            t0 = time.time()

            # Per-file timeout to prevent hangs
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(recognize_raga, audio_path, AGG_FOLDER, models)
                    result = future.result(timeout=PER_FILE_TIMEOUT)
            except TimeoutError:
                print(f"T [{total_files:2d}] {file:<35} | TIMEOUT after {time.time()-t0:.0f}s")
                result = {"final": "UNKNOWN / LOW CONFIDENCE", "ranking": [], "margin": 0.0, "confidence_tier": "UNKNOWN"}
            except Exception as e:
                print(f"E [{total_files:2d}] {file:<35} | ERROR: {str(e)[:40]}")
                result = {"final": "UNKNOWN / LOW CONFIDENCE", "ranking": [], "margin": 0.0, "confidence_tier": "UNKNOWN"}'''

c = c.replace(old_call, new_call)

# 4. Add elapsed time + counter to print line
old_print = '''            status_sym = "+" if is_correct else ("?" if "UNKNOWN" in final else "X")
            print(f"{status_sym} {file:<35} | True={raga_folder:<20} | Pred={final:<25} "
                  f"| Tier={confidence_tier:<10} | Margin={round(margin, 4)}")'''

new_print = '''            elapsed = time.time() - t0
            status_sym = "+" if is_correct else ("?" if "UNKNOWN" in final else "X")
            print(f"{status_sym} [{total_files:2d}] {file:<35} | True={raga_folder:<18} | Pred={final:<25} "
                  f"| Tier={confidence_tier:<8} | M={round(margin, 4)} ({elapsed:.0f}s)")'''

c = c.replace(old_print, new_print)

# 5. Fix unicode in error message
c = c.replace('\u2717 No models', 'No models')

# 6. Fix unicode dash in header
c = c.replace('v1.2 \u2014 Seed', 'v1.2.5 -- Seed')

with open("batch_evaluate.py", "w", encoding="utf-8") as f:
    f.write(c)

# Verify
with open("batch_evaluate.py", "r", encoding="utf-8") as f:
    v = f.read()

checks = [
    ("import time", "import time" in v),
    ("ThreadPoolExecutor", "ThreadPoolExecutor" in v),
    ("PER_FILE_TIMEOUT", "PER_FILE_TIMEOUT = 360" in v),
    ("future.result(timeout", "future.result(timeout" in v),
    ("elapsed time print", "elapsed:.0f" in v),
    ("no unicode", "\u2717" not in v and "\u2014" not in v),
]
all_ok = True
for label, ok in checks:
    print("[{}] {}".format("OK" if ok else "FAIL", label))
    if not ok:
        all_ok = False

print()
print("PATCH DONE" if all_ok else "PATCH HAD ISSUES")
