"""
Diagnostic: Mohanam same-song duplicates + Bhairavi wrong predictions.
Also checks Kamboji duplicates.
"""
import os, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
AUDIO_DIR = r"D:\Swaragam\datasets\seed_carnatic"
EPS = 1e-8

def load_features(raga_filter=None):
    clips = []
    for fname in sorted(os.listdir(FEAT_DIR)):
        if not fname.endswith(".npz"):
            continue
        fpath = os.path.join(FEAT_DIR, fname)
        if os.path.isdir(fpath):
            continue
        data = np.load(fpath, allow_pickle=True)
        if "feature_version" not in data or str(data["feature_version"]) != "v1.2":
            continue
        if float(data["gating_ratio"]) < 0.05:
            continue
        raga = str(data["raga"])
        if raga_filter and raga not in raga_filter:
            continue
        cents = data["cents_gated"]
        if len(cents) < 200:
            continue

        hist, _ = np.histogram(cents, bins=72, range=(0, 1200))
        pcd = hist / (np.sum(hist) + EPS)

        clips.append({
            "fname": fname,
            "raga": raga,
            "pcd": pcd,
            "sa_hz": float(data["sa_hz"]),
            "gating": float(data["gating_ratio"]),
            "n_frames": len(cents),
        })
    return clips

# ============================================================
# 1. MOHANAM SAME-SONG AUDIT
# ============================================================
print("=" * 70)
print("1. MOHANAM SAME-SONG AUDIT")
print("=" * 70)

mohanam_audio = sorted(os.listdir(os.path.join(AUDIO_DIR, "Mohanam")))
print("\nAudio files ({} total):".format(len(mohanam_audio)))

# Group by song name (strip suffix like .demucs-vocal.wav, .vocal.mp3, .vocal-s.mp3)
song_groups = defaultdict(list)
for f in mohanam_audio:
    base = f
    for suffix in [".demucs-vocal.wav", ".vocal-s.mp3", ".vocal.mp3", ".mp3", ".wav", ".mp4"]:
        if base.lower().endswith(suffix):
            base = base[:-len(suffix)]
            break
    song_groups[base].append(f)

print("\nSong groups:")
for song, files in sorted(song_groups.items()):
    dup_marker = " ** DUPLICATE" if len(files) > 1 else ""
    print("  {} ({} files){}".format(song, len(files), dup_marker))
    for f in files:
        print("    - {}".format(f))

unique_songs = len(song_groups)
dup_songs = sum(1 for files in song_groups.values() if len(files) > 1)
print("\nUnique songs: {} | Songs with duplicates: {}".format(unique_songs, dup_songs))

# Check tonic consistency for duplicate songs
mohanam_feats = load_features({"Mohanam"})
print("\nTonic (Sa) check across Mohanam features ({} clips):".format(len(mohanam_feats)))
for c in mohanam_feats:
    print("  {:60s} Sa={:.1f} Hz  gating={:.3f}  frames={}".format(
        c["fname"][:60], c["sa_hz"], c["gating"], c["n_frames"]))

# ============================================================
# 2. KAMBOJI SAME-SONG AUDIT
# ============================================================
print("\n" + "=" * 70)
print("2. KAMBOJI SAME-SONG AUDIT")
print("=" * 70)

kamboji_audio = sorted(os.listdir(os.path.join(AUDIO_DIR, "Kamboji")))
song_groups_k = defaultdict(list)
for f in kamboji_audio:
    base = f
    for suffix in [".demucs-vocal.wav", ".vocal-s.mp3", ".vocal.mp3", ".mp3", ".wav"]:
        if base.lower().endswith(suffix):
            base = base[:-len(suffix)]
            break
    song_groups_k[base].append(f)

print("\nSong groups:")
for song, files in sorted(song_groups_k.items()):
    dup_marker = " ** DUPLICATE" if len(files) > 1 else ""
    print("  {} ({} files){}".format(song, len(files), dup_marker))
    for f in files:
        print("    - {}".format(f))

# ============================================================
# 3. BHAIRAVI WRONG PREDICTIONS INVESTIGATION
# ============================================================
print("\n" + "=" * 70)
print("3. BHAIRAVI INVESTIGATION")
print("=" * 70)

bhairavi_feats = load_features({"Bhairavi"})
all_feats = load_features()

# Compute mean PCD per raga (for comparison)
raga_pcds = defaultdict(list)
for c in all_feats:
    raga_pcds[c["raga"]].append(c["pcd"])
raga_means = {r: np.mean(pcds, axis=0) for r, pcds in raga_pcds.items()}

print("\nBhairavi clips - tonic and similarity to each raga model:")
print("{:50s} {:>8s}  {:>8s}  {:>8s}  {:>8s}  {:>8s}  {:>8s}  {:>8s}".format(
    "File", "Sa Hz", "Bhair", "Kalyan", "Thodi", "Shank", "Mohan", "Kambo"))

for c in bhairavi_feats:
    sims = {}
    for raga, mean_pcd in raga_means.items():
        sims[raga] = np.dot(c["pcd"], mean_pcd)
    print("{:50s} {:>8.1f}  {:.5f}  {:.5f}  {:.5f}  {:.5f}  {:.5f}  {:.5f}".format(
        c["fname"][:50], c["sa_hz"],
        sims.get("Bhairavi", 0), sims.get("Kalyani", 0),
        sims.get("Thodi", 0), sims.get("Shankarabharanam", 0),
        sims.get("Mohanam", 0), sims.get("Kamboji", 0)))

# PCD entropy check
print("\nPCD entropy per raga (higher = more spread out):")
for raga in sorted(raga_means.keys()):
    pcd = raga_means[raga]
    pcd_safe = pcd[pcd > 0]
    entropy = -np.sum(pcd_safe * np.log2(pcd_safe))
    n_active = np.sum(pcd > 0.005)
    print("  {:20s} entropy={:.3f}  active_bins={}".format(raga, entropy, int(n_active)))

# Compare Bhairavi vs Thodi PCD overlap
bhairavi_mean = raga_means["Bhairavi"]
thodi_mean = raga_means["Thodi"]
kalyani_mean = raga_means["Kalyani"]

overlap_bt = np.sum(np.minimum(bhairavi_mean, thodi_mean))
overlap_bk = np.sum(np.minimum(bhairavi_mean, kalyani_mean))
print("\nPCD overlap (sum of min):")
print("  Bhairavi-Thodi:     {:.4f}".format(overlap_bt))
print("  Bhairavi-Kalyani:   {:.4f}".format(overlap_bk))
print("  Bhairavi self-dot:  {:.4f}".format(np.dot(bhairavi_mean, bhairavi_mean)))
print("  Thodi self-dot:     {:.4f}".format(np.dot(thodi_mean, thodi_mean)))
print("  Kalyani self-dot:   {:.4f}".format(np.dot(kalyani_mean, kalyani_mean)))

# ============================================================
# 4. SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

# Mohanam duplicates
print("\nMOHANAM:")
for song, files in sorted(song_groups.items()):
    if len(files) > 1:
        print("  DUPLICATE: {} -> {} files (keep best, remove rest)".format(song, len(files)))

# Kamboji duplicates
print("\nKAMBOJI:")
for song, files in sorted(song_groups_k.items()):
    if len(files) > 1:
        print("  DUPLICATE: {} -> {} files".format(song, len(files)))

print("\nDone.")
