"""
Extract features for NEW clips only (skip files that already have features).
Targets: new Kamboji, Mohanam, Saveri, Abhogi, Madhyamavati, Hamsadhvani clips.
"""
import os, librosa, numpy as np
from datetime import datetime
import sys
sys.path.insert(0, r"D:\Swaragam\scripts")
from utils import estimate_tonic

SR = 22050
MAX_DURATION_SEC = 360
FMIN = librosa.note_to_hz("C1")
FMAX = librosa.note_to_hz("C6")
FEATURE_VERSION = "v1.2"
WINDOW_SIZE = 10
DRIFT_THRESHOLD = 25
VOICED_RATIO_THRESHOLD = 0.6
EPS = 1e-8

DATASET_DIR = r"D:\Swaragam\datasets\seed_carnatic"
FEATURE_DIR = r"D:\Swaragam\pcd_results\features_v12"
os.makedirs(FEATURE_DIR, exist_ok=True)

# Get list of already-extracted base names
existing_features = set()
for f in os.listdir(FEATURE_DIR):
    if f.endswith('.npz'):
        # Remove timestamp suffix: name_YYYYMMDD_HHMMSS.npz
        parts = f.rsplit('_', 2)
        if len(parts) >= 3:
            base = parts[0]
            existing_features.add(base.lower())

def apply_pitch_stability_gate(f0, sa_hz, voiced_flag):
    cents = np.zeros_like(f0)
    valid_idx = np.where(~np.isnan(f0))[0]
    cents[valid_idx] = 1200 * np.log2(f0[valid_idx] / sa_hz)
    cents = np.mod(cents, 1200)
    gated_mask = np.zeros_like(f0, dtype=bool)
    for i in range(0, len(f0) - WINDOW_SIZE):
        window = cents[i:i+WINDOW_SIZE]
        voiced_window = voiced_flag[i:i+WINDOW_SIZE]
        if np.mean(voiced_window) < VOICED_RATIO_THRESHOLD:
            continue
        c1 = np.mean(window[:WINDOW_SIZE//2])
        c2 = np.mean(window[WINDOW_SIZE//2:])
        drift = abs(c2 - c1)
        if drift < DRIFT_THRESHOLD:
            gated_mask[i:i+WINDOW_SIZE] = True
    gated_cents = cents[gated_mask]
    gating_ratio = np.sum(gated_mask) / (np.sum(voiced_flag) + EPS)
    return gated_cents, gating_ratio

def process_file(audio_path, raga_label):
    y, sr = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)
    f0, voiced_flag, _ = librosa.pyin(y, fmin=FMIN, fmax=FMAX, sr=sr)
    valid_f0 = f0[~np.isnan(f0)]
    if len(valid_f0) == 0:
        print("  SKIP (no voiced): {}".format(os.path.basename(audio_path)))
        return None
    
    # C1: canonical tonic from utils.py
    sa_hz = estimate_tonic(valid_f0)
    
    cents_gated, gating_ratio = apply_pitch_stability_gate(f0, sa_hz, voiced_flag)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    out_path = os.path.join(FEATURE_DIR, "{}_{}.npz".format(base_name, timestamp))
    
    np.savez(out_path,
        feature_version=FEATURE_VERSION, raga=raga_label,
        sa_hz=sa_hz, f0=f0, voiced_flag=voiced_flag,
        cents_gated=cents_gated, gating_ratio=gating_ratio,
        window_size=WINDOW_SIZE, drift_threshold=DRIFT_THRESHOLD,
        voiced_ratio_threshold=VOICED_RATIO_THRESHOLD)
    
    print("  OK: {} | gating={:.3f} | sa={:.1f}Hz | frames={}".format(
        base_name[:50], gating_ratio, sa_hz, len(cents_gated)))
    return gating_ratio

# Main
print("=" * 80)
print("FEATURE EXTRACTION — New Clips Only")
print("=" * 80)
print()

total = 0
skipped = 0
extracted = 0

for raga_folder in sorted(os.listdir(DATASET_DIR)):
    raga_path = os.path.join(DATASET_DIR, raga_folder)
    if not os.path.isdir(raga_path):
        continue
    
    new_files = []
    for f in sorted(os.listdir(raga_path)):
        if not f.lower().endswith(('.wav', '.mp3', '.flac', '.mp4', '.m4a')):
            continue
        # Check if already extracted
        base = os.path.splitext(f)[0].lower()
        # Also strip .mp3 from .mp3.mp3 type names
        if base.endswith('.mp3'):
            base = base[:-4]
        if any(base[:20] in existing for existing in existing_features):
            skipped += 1
            continue
        new_files.append(f)
    
    if new_files:
        print("{} ({} new files):".format(raga_folder, len(new_files)))
        for f in new_files:
            total += 1
            audio_path = os.path.join(raga_path, f)
            ratio = process_file(audio_path, raga_folder)
            if ratio is not None:
                extracted += 1
        print()

print("=" * 80)
print("EXTRACTION SUMMARY")
print("=" * 80)
print("  Already had features: {}".format(skipped))
print("  New files processed:  {}".format(total))
print("  Successfully extracted: {}".format(extracted))
print()

# Show all feature counts per raga
raga_counts = {}
for f in os.listdir(FEATURE_DIR):
    if not f.endswith('.npz'):
        continue
    data = np.load(os.path.join(FEATURE_DIR, f), allow_pickle=True)
    if "feature_version" in data and str(data["feature_version"]) == "v1.2":
        raga = str(data["raga"])
        raga_counts[raga] = raga_counts.get(raga, 0) + 1

print("Feature counts per raga:")
for raga in sorted(raga_counts.keys()):
    print("  {:20} {:3d} features".format(raga, raga_counts[raga]))
print("  {:20} {:3d} TOTAL".format("---", sum(raga_counts.values())))

print()
print("NEXT: Re-aggregate with 72 bins, then LOO validate")
print("Done.")
