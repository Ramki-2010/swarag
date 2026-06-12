"""Quick diagnostic: Where do swaras actually land in the 72-bin PCD?"""
import os, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
N_BINS = 72
EPS = 1e-8
MODELED = {"Bhairavi", "Kalyani", "Mohanam", "Shankarabharanam", "Thodi", "Abhogi", "Saveri"}

# Load all clips and compute mean PCD per raga
raga_pcds = defaultdict(list)
for f in sorted(os.listdir(FEAT_DIR)):
    if not f.endswith(".npz"):
        continue
    fpath = os.path.join(FEAT_DIR, f)
    if os.path.isdir(fpath):
        continue
    d = np.load(fpath, allow_pickle=True)
    if str(d.get("feature_version", "")) != "v1.2":
        continue
    raga = str(d["raga"])
    if raga not in MODELED:
        continue
    cents = d["cents_gated"]
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)
    raga_pcds[raga].append(pcd)

print("Top 10 bins per raga (bin index, cents center, energy):\n")
for raga in sorted(raga_pcds.keys()):
    mean_pcd = np.mean(raga_pcds[raga], axis=0)
    top_bins = np.argsort(mean_pcd)[::-1][:10]
    print("{}:".format(raga))
    for b in top_bins:
        cents = b * (1200.0 / N_BINS)
        print("  bin {:2d} = {:6.1f} cents  energy={:.4f}".format(b, cents, mean_pcd[b]))
    print()
