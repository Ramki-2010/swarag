"""
Test per-raga dyad weight overrides for Abhogi and Bhairavi.
Both are weak because their identity is in transitions, not just PCD.
Abhogi: janya of Kalyani (same swaras, different phrases)
Bhairavi: shares komal swaras with Thodi (PCD overlap 78%)
"""
import os, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
N_BINS = 72
ALPHA = 0.01
EPS = 1e-8
MIN_STABLE = 5

MODELED = {"Bhairavi", "Kalyani", "Mohanam", "Shankarabharanam", "Thodi", "Abhogi", "Saveri"}

def extract_features(data):
    cents = data["cents_gated"]
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)
    bins = np.floor(cents / (1200.0 / N_BINS)).astype(int)
    bins = np.clip(bins, 0, N_BINS - 1)
    up = np.zeros((N_BINS, N_BINS))
    down = np.zeros((N_BINS, N_BINS))
    i = 0
    while i < len(bins):
        j = i + 1
        while j < len(bins) and bins[j] == bins[i]:
            j += 1
        if (j - i) >= MIN_STABLE and i > 0:
            prev, curr = bins[i - 1], bins[i]
            if curr > prev: up[prev, curr] += 1
            elif curr < prev: down[prev, curr] += 1
        i = j
    up_flat = (up + ALPHA).flatten()
    up_flat /= (np.sum(up_flat) + EPS)
    down_flat = (down + ALPHA).flatten()
    down_flat /= (np.sum(down_flat) + EPS)
    return pcd, up_flat, down_flat

# Load clips
clips = []
for f in sorted(os.listdir(FEAT_DIR)):
    if not f.endswith(".npz"):
        continue
    fpath = os.path.join(FEAT_DIR, f)
    if os.path.isdir(fpath):
        continue
    d = np.load(fpath, allow_pickle=True)
    if str(d.get("feature_version", "")) != "v1.2":
        continue
    if float(d["gating_ratio"]) < 0.05:
        continue
    raga = str(d["raga"])
    if raga not in MODELED:
        continue
    cents = d["cents_gated"]
    if len(cents) < 200:
        continue
    pcd, up, down = extract_features(d)
    clips.append({"fname": f, "raga": raga, "pcd": pcd, "up": up, "down": down})

print("Loaded {} clips across {} ragas".format(len(clips), len(MODELED)))
print()


def run_loo(clips, base_pcd_w=0.8, base_dyad_w=0.2, overrides=None, margin_thresh=0.001, label=""):
    """
    overrides: dict of {raga: (pcd_w, dyad_w)} for per-raga scoring overrides.
    When scoring a clip against raga R, if R is in overrides, use those weights.
    """
    if overrides is None:
        overrides = {}
    
    correct = 0; wrong = 0; unknown = 0
    raga_stats = defaultdict(lambda: {"c": 0, "w": 0, "u": 0})
    wrong_to = defaultdict(int)

    for i, held in enumerate(clips):
        train = [c for j, c in enumerate(clips) if j != i]
        raga_pcds = defaultdict(list)
        raga_ups = defaultdict(list)
        raga_downs = defaultdict(list)
        for c in train:
            raga_pcds[c["raga"]].append(c["pcd"])
            raga_ups[c["raga"]].append(c["up"])
            raga_downs[c["raga"]].append(c["down"])

        raga_mean_pcd = {r: np.mean(v, axis=0) for r, v in raga_pcds.items()}
        raga_mean_up = {r: np.mean(v, axis=0) for r, v in raga_ups.items()}
        raga_mean_down = {r: np.mean(v, axis=0) for r, v in raga_downs.items()}

        all_pcds_arr = np.array(list(raga_mean_pcd.values()))
        doc_freq = np.sum(all_pcds_arr > 0.001, axis=0) + 1
        idf = np.log(len(raga_mean_pcd) / doc_freq)
        std = np.std(all_pcds_arr, axis=0)
        weights = idf / (std + EPS)
        weights = weights / (np.sum(weights) + EPS) * N_BINS

        scores = {}
        for r in raga_mean_pcd:
            pcd_w, dyad_w = overrides.get(r, (base_pcd_w, base_dyad_w))
            
            pcd_weighted_test = held["pcd"] * weights
            pcd_weighted_test /= (np.sum(pcd_weighted_test) + EPS)
            pcd_weighted_model = raga_mean_pcd[r] * weights
            pcd_weighted_model /= (np.sum(pcd_weighted_model) + EPS)
            
            pcd_score = np.dot(pcd_weighted_test, pcd_weighted_model)
            dyad_score = (np.dot(held["up"], raga_mean_up[r]) +
                          np.dot(held["down"], raga_mean_down[r])) / 2
            scores[r] = pcd_w * pcd_score + dyad_w * dyad_score

        ranking = sorted(scores.items(), key=lambda x: -x[1])
        margin = ranking[0][1] - ranking[1][1] if len(ranking) >= 2 else 0

        pred = ranking[0][0] if margin >= margin_thresh else "UNKNOWN"

        rs = raga_stats[held["raga"]]
        if pred == "UNKNOWN":
            unknown += 1; rs["u"] += 1
        elif pred == held["raga"]:
            correct += 1; rs["c"] += 1
        else:
            wrong += 1; rs["w"] += 1
            wrong_to[ranking[0][0]] += 1

    decided = correct + wrong
    acc = correct / decided if decided > 0 else 0

    print("{:55s} C={:2d} W={:2d} U={:2d} Acc={:.1f}%".format(label, correct, wrong, unknown, acc * 100))
    for r in sorted(raga_stats.keys()):
        s = raga_stats[r]
        d = s["c"] + s["w"]
        a = s["c"] / d * 100 if d > 0 else 0
        print("  {:20s} {:2d}c {:2d}w {:2d}u ({:.0f}%)".format(r, s["c"], s["w"], s["u"], a))
    if wrong_to:
        sinks = ", ".join("{}={}".format(r, c) for r, c in sorted(wrong_to.items(), key=lambda x: -x[1])[:4])
        print("  Sink: {}".format(sinks))
    print()
    return acc


print("=" * 80)
print("BASELINE (0.8/0.2 global)")
print("=" * 80)
run_loo(clips, 0.8, 0.2, label="Baseline 0.8/0.2")

print("=" * 80)
print("ABHOGI OVERRIDES (dyad-heavy for Abhogi only)")
print("=" * 80)
run_loo(clips, 0.8, 0.2, overrides={"Abhogi": (0.6, 0.4)}, label="Abhogi=0.6/0.4")
run_loo(clips, 0.8, 0.2, overrides={"Abhogi": (0.5, 0.5)}, label="Abhogi=0.5/0.5")
run_loo(clips, 0.8, 0.2, overrides={"Abhogi": (0.4, 0.6)}, label="Abhogi=0.4/0.6")

print("=" * 80)
print("BHAIRAVI OVERRIDES (dyad-heavy for Bhairavi only)")
print("=" * 80)
run_loo(clips, 0.8, 0.2, overrides={"Bhairavi": (0.6, 0.4)}, label="Bhairavi=0.6/0.4")
run_loo(clips, 0.8, 0.2, overrides={"Bhairavi": (0.5, 0.5)}, label="Bhairavi=0.5/0.5")

print("=" * 80)
print("COMBINED OVERRIDES (both Abhogi + Bhairavi)")
print("=" * 80)
run_loo(clips, 0.8, 0.2, overrides={"Abhogi": (0.5, 0.5), "Bhairavi": (0.6, 0.4)}, label="Abhogi=0.5/0.5 + Bhairavi=0.6/0.4")
run_loo(clips, 0.8, 0.2, overrides={"Abhogi": (0.4, 0.6), "Bhairavi": (0.5, 0.5)}, label="Abhogi=0.4/0.6 + Bhairavi=0.5/0.5")

print("=" * 80)
print("MOHANAM OVERRIDE (test if dyads help)")
print("=" * 80)
run_loo(clips, 0.8, 0.2, overrides={"Mohanam": (0.6, 0.4)}, label="Mohanam=0.6/0.4")
run_loo(clips, 0.8, 0.2, overrides={"Mohanam": (0.5, 0.5)}, label="Mohanam=0.5/0.5")
