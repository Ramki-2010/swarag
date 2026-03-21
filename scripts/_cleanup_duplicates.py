"""
CLEANUP: Move duplicate features to excluded/, delete .dup files,
then re-aggregate and run LOO validation.
"""
import os, shutil, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
EXCL_DIR = os.path.join(FEAT_DIR, "excluded")
os.makedirs(EXCL_DIR, exist_ok=True)

# === PHASE 1: Move duplicate features to excluded/ ===

DUPLICATES_TO_REMOVE = [
    "Brochevarevarura.demucs-vocal_20260320_005950.npz",
    "Dinamani Vamsa.demucs-vocal_20260320_004359.npz",
    "Enadhu Manam Kavalai.vocal-s_20260320_004948.npz",
    "Kari Kalabha Mukham.demucs-vocal_20260320_011509.npz",
    "Nannu Brova Neeku.demucs-vocal_20260320_003046.npz",
    "Nannu Brova Neeku.vocal-s_20260320_003438.npz",
    "Rama Namam Bhajare.demucs-vocal_20260320_005406.npz",
    "Sarasuda Ninne Kori.demucs-vocal_20260320_011944.npz",
    "Shankari Shankuru.vocal_20260320_012648.npz",
    "Shloka Namaste Sarvalokaanam.demucs-vocal_20260320_010713.npz",
    "Shloka Namaste Sarvalokaanam.vocal_20260320_011107.npz",
    "Shlokam Shivah Shaktyayukto.demucs-vocal_20260320_005620.npz",
    "kamalambike.vocal_20260320_013057.npz",
]

print("=" * 80)
print("PHASE 1: MOVE DUPLICATE FEATURES TO excluded/")
print("=" * 80)
moved = 0
for fname in DUPLICATES_TO_REMOVE:
    src = os.path.join(FEAT_DIR, fname)
    dst = os.path.join(EXCL_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, dst)
        print("  MOVED: {}".format(fname[:70]))
        moved += 1
    else:
        print("  SKIP (not found): {}".format(fname[:70]))
print("Moved: {}/{}".format(moved, len(DUPLICATES_TO_REMOVE)))

# === PHASE 2: Delete .npz.dup files ===
print()
print("=" * 80)
print("PHASE 2: DELETE .npz.dup FILES")
print("=" * 80)
deleted = 0
for fname in sorted(os.listdir(FEAT_DIR)):
    if fname.endswith('.npz.dup'):
        fpath = os.path.join(FEAT_DIR, fname)
        os.remove(fpath)
        print("  DELETED: {}".format(fname[:70]))
        deleted += 1
print("Deleted: {}".format(deleted))

# === PHASE 3: Verify clean state ===
print()
print("=" * 80)
print("PHASE 3: VERIFY CLEAN STATE")
print("=" * 80)

raga_counts = defaultdict(int)
total = 0
for fname in sorted(os.listdir(FEAT_DIR)):
    if not fname.endswith('.npz'):
        continue
    fpath = os.path.join(FEAT_DIR, fname)
    if os.path.isdir(fpath):
        continue
    try:
        data = np.load(fpath, allow_pickle=True)
        if str(data.get("feature_version", "")) != "v1.2":
            continue
        if float(data.get("gating_ratio", 0)) < 0.05:
            continue
        raga = str(data["raga"])
        raga_counts[raga] += 1
        total += 1
    except:
        pass

print("Clean feature counts:")
for raga in sorted(raga_counts.keys()):
    print("  {:20s} {:3d} clips".format(raga, raga_counts[raga]))
print("  {:20s} {:3d} TOTAL".format("---", total))
print()

# Check for any remaining duplicates
print("Remaining .npz.dup files: {}".format(
    len([f for f in os.listdir(FEAT_DIR) if f.endswith('.npz.dup')])))
print("Remaining non-.npz non-dir: {}".format(
    len([f for f in os.listdir(FEAT_DIR) 
         if not f.endswith('.npz') and not os.path.isdir(os.path.join(FEAT_DIR, f))])))

print()
print("CLEANUP COMPLETE. Ready for re-aggregation.")
