"""
Run Demucs vocal isolation on all staged mix files.
Processes each raga folder, extracts vocals, copies to seed_carnatic.
"""
import os
import subprocess
import shutil

DEMUCS_PYTHON = r"D:\Swaragam\demucs_env\Scripts\python.exe"
STAGING_DIR = r"D:\Swaragam\demucs_staging"
DEMUCS_OUTPUT = r"D:\Swaragam\demucs_outputs\saraga_batch"
SEED_DIR = r"D:\Swaragam\datasets\seed_carnatic"

print("=" * 80)
print("DEMUCS VOCAL ISOLATION — Saraga Mix Files")
print("=" * 80)
print()

# Collect all mix files
mix_files = []
for raga_dir in sorted(os.listdir(STAGING_DIR)):
    raga_path = os.path.join(STAGING_DIR, raga_dir)
    if not os.path.isdir(raga_path):
        continue
    for f in sorted(os.listdir(raga_path)):
        if f.endswith('.mp3'):
            mix_files.append((raga_dir, os.path.join(raga_path, f), f))

print("Files to process: {}".format(len(mix_files)))
for raga, path, fname in mix_files:
    size = round(os.path.getsize(path) / (1024*1024), 1)
    print("  [{}] {} ({:.1f}MB)".format(raga, fname, size))
print()

# Process each file
results = []
for i, (raga, filepath, fname) in enumerate(mix_files):
    print("[{}/{}] Processing: {} ({})".format(i+1, len(mix_files), fname, raga))
    
    cmd = [
        DEMUCS_PYTHON, "-m", "demucs",
        "--two-stems", "vocals",
        "-o", DEMUCS_OUTPUT,
        filepath
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print("  Demucs OK")
            
            # Find the vocal output file
            # Demucs output: {output_dir}/htdemucs/{stem_name}/vocals.wav
            stem_name = os.path.splitext(fname)[0]
            if stem_name.endswith('.mp3'):
                stem_name = stem_name[:-4]  # Handle .mp3.mp3 naming
            
            vocal_candidates = []
            for root, dirs, files in os.walk(DEMUCS_OUTPUT):
                for f in files:
                    if 'vocal' in f.lower() and stem_name.lower()[:20] in root.lower():
                        vocal_candidates.append(os.path.join(root, f))
            
            if not vocal_candidates:
                # Broader search
                for root, dirs, files in os.walk(DEMUCS_OUTPUT):
                    for f in files:
                        if 'vocal' in f.lower():
                            full = os.path.join(root, f)
                            # Check if it's new (created in last 5 min)
                            if os.path.getmtime(full) > os.path.getmtime(filepath) - 10:
                                vocal_candidates.append(full)
            
            if vocal_candidates:
                vocal_path = sorted(vocal_candidates)[-1]  # Latest
                
                # Copy to seed_carnatic
                dest_dir = os.path.join(SEED_DIR, raga)
                os.makedirs(dest_dir, exist_ok=True)
                
                out_name = stem_name.replace('.mix', '') + ".demucs-vocal.mp3"
                dest_path = os.path.join(dest_dir, out_name)
                
                # Convert wav to mp3 if needed, or just copy
                if vocal_path.endswith('.wav'):
                    # Just copy the wav, recognition handles both formats
                    out_name = stem_name.replace('.mix', '') + ".demucs-vocal.wav"
                    dest_path = os.path.join(dest_dir, out_name)
                
                shutil.copy2(vocal_path, dest_path)
                size = round(os.path.getsize(dest_path) / (1024*1024), 1)
                print("  Copied: {} ({:.1f}MB)".format(out_name, size))
                results.append((raga, out_name, "OK"))
            else:
                print("  WARNING: Vocal output not found")
                results.append((raga, fname, "NO VOCAL"))
        else:
            print("  ERROR: {}".format(result.stderr[:200]))
            results.append((raga, fname, "DEMUCS FAIL"))
    except subprocess.TimeoutExpired:
        print("  TIMEOUT (>10 min)")
        results.append((raga, fname, "TIMEOUT"))
    except Exception as e:
        print("  ERROR: {}".format(str(e)[:200]))
        results.append((raga, fname, "ERROR"))

# Summary
print()
print("=" * 80)
print("DEMUCS RESULTS")
print("=" * 80)
ok = sum(1 for r in results if r[2] == "OK")
fail = len(results) - ok
print("  Success: {}/{}".format(ok, len(results)))
if fail > 0:
    print("  Failed:")
    for raga, fname, status in results:
        if status != "OK":
            print("    [{}] {} - {}".format(raga, fname, status))

# Final clip counts
print()
print("=" * 80)
print("FINAL CLIP COUNTS (after Demucs)")
print("=" * 80)
for raga in ['Kamboji', 'Mohanam', 'Saveri', 'Abhogi', 'Madhyamavati', 'Hamsadhvani',
             'Bhairavi', 'Kalyani', 'Shankarabharanam', 'Thodi']:
    raga_dir = os.path.join(SEED_DIR, raga)
    if os.path.exists(raga_dir):
        clips = [f for f in os.listdir(raga_dir) 
                 if f.endswith('.mp3') or f.endswith('.wav')]
        print("  {:20} {:3d} clips".format(raga, len(clips)))

print()
print("NEXT: Run feature extraction on new clips")
print("Done.")
