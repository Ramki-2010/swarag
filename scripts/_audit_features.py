"""
Audit all feature files to identify duplicates.
Same song with multiple vocal isolation versions = duplicate.
"""
import os, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"

# Load all feature files
all_files = []
for fname in sorted(os.listdir(FEAT_DIR)):
    fpath = os.path.join(FEAT_DIR, fname)
    if os.path.isdir(fpath):
        continue
    if fname.endswith('.npz.dup'):
        all_files.append({"fname": fname, "type": "DUP_FILE"})
        continue
    if not fname.endswith('.npz'):
        continue
    try:
        data = np.load(fpath, allow_pickle=True)
        raga = str(data.get("raga", "?"))
        ver = str(data.get("feature_version", "?"))
        gating = float(data.get("gating_ratio", 0))
        frames = len(data.get("cents_gated", []))
        all_files.append({
            "fname": fname, "type": "FEATURE",
            "raga": raga, "version": ver,
            "gating": gating, "frames": frames
        })
    except Exception as e:
        all_files.append({"fname": fname, "type": "ERROR"})

# Group by raga
raga_files = defaultdict(list)
dup_files = []
for f in all_files:
    if f["type"] == "DUP_FILE":
        dup_files.append(f["fname"])
    elif f["type"] == "FEATURE" and f["version"] == "v1.2":
        raga_files[f["raga"]].append(f)

print("=" * 90)
print("FEATURE INVENTORY")
print("=" * 90)
total = 0
for raga in sorted(raga_files.keys()):
    files = raga_files[raga]
    total += len(files)
    print("\n{} ({} features):".format(raga, len(files)))
    for f in files:
        print("  {:72s} g={:.3f} fr={:5d}".format(
            f["fname"][:72], f["gating"], f["frames"]))

print("\n\nTotal v1.2 features: {}".format(total))
print("Total .npz.dup files: {}".format(len(dup_files)))
for d in dup_files:
    print("  DUP: {}".format(d))

# Identify duplicates: same song, different vocal isolation
print("\n" + "=" * 90)
print("DUPLICATE DETECTION (same song, different vocal version)")
print("=" * 90)

total_dups = 0
dup_to_remove = []

for raga in sorted(raga_files.keys()):
    files = raga_files[raga]
    song_groups = defaultdict(list)
    for f in files:
        name = f["fname"]
        # Remove timestamp suffix (_YYYYMMDD_HHMMSS.npz)
        parts = name.rsplit("_", 2)
        if len(parts) >= 3:
            base = parts[0]
        else:
            base = name.replace(".npz", "")
        # Normalize: remove vocal isolation suffixes
        normalized = base
        for suffix in [".demucs-vocal", ".vocal-s", ".vocal"]:
            normalized = normalized.replace(suffix, "")
        song_groups[normalized.lower()].append(f)

    dups = {k: v for k, v in song_groups.items() if len(v) > 1}
    if dups:
        print("\n{} -- DUPLICATES:".format(raga))
        for song, versions in sorted(dups.items()):
            print("  Song: {}".format(song))
            # Pick best: prefer .vocal (stem) over .demucs-vocal, highest gating
            best = None
            for v in versions:
                is_stem = ".vocal_" in v["fname"] or ".vocal-s_" in v["fname"]
                is_demucs = ".demucs-vocal_" in v["fname"]
                score = v["gating"] + (0.1 if is_stem else 0)
                tag = "STEM" if is_stem else ("DEMUCS" if is_demucs else "OTHER")
                if best is None or score > best[1]:
                    best = (v, score, tag)
                print("    {} {:60s} g={:.3f} fr={}".format(
                    tag, v["fname"][:60], v["gating"], v["frames"]))

            # Mark non-best for removal
            for v in versions:
                if v["fname"] != best[0]["fname"]:
                    dup_to_remove.append(v["fname"])
                    total_dups += 1
            print("    KEEP: {} ({})".format(best[0]["fname"][:60], best[2]))

print("\n" + "=" * 90)
print("CLEANUP PLAN")
print("=" * 90)
print("Features to REMOVE (move to excluded/): {}".format(len(dup_to_remove)))
for f in sorted(dup_to_remove):
    print("  REMOVE: {}".format(f))
print("\n.npz.dup files to DELETE: {}".format(len(dup_files)))
print("\nAfter cleanup: {} unique features".format(total - total_dups))

# Also count per-raga after cleanup
print("\nPer-raga counts AFTER cleanup:")
for raga in sorted(raga_files.keys()):
    files = raga_files[raga]
    removed = sum(1 for f in files if f["fname"] in dup_to_remove)
    print("  {:20s} {:3d} -> {:3d}".format(raga, len(files), len(files) - removed))
