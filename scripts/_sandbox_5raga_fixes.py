"""
Sandbox: Test 3 fixes for 5-raga model (55.8% baseline).
A) Per-raga adaptive margins
B) Higher dyad weight (0.5/0.5, 0.4/0.6)
C) Remove weak Mohanam clip (Shloka Sri Ramachandra, 936 frames)
D) Combinations
"""
import os, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
N_BINS = 72
ALPHA = 0.01
EPS = 1e-8
MIN_STABLE = 5

MODELED = {"Bhairavi", "Kalyani", "Mohanam", "Shankarabharanam", "Thodi"}

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
        run_len = j - i
        if run_len >= MIN_STABLE and i > 0:
            prev = bins[i - 1]
            curr = bins[i]
            if curr > prev:
                up[prev, curr] += 1
            elif curr < prev:
                down[prev, curr] += 1
        i = j

    up_flat = (up + ALPHA).flatten()
    up_flat = up_flat / (np.sum(up_flat) + EPS)
    down_flat = (down + ALPHA).flatten()
    down_flat = down_flat / (np.sum(down_flat) + EPS)

    return pcd, up_flat, down_flat

# Load clips
all_clips = []
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
    all_clips.append({
        "fname": f, "raga": raga, "pcd": pcd, "up": up, "down": down,
        "n_frames": len(cents)
    })

print("Total clips: {}".format(len(all_clips)))


def run_loo(clips, pcd_w=0.6, dyad_w=0.4, margin_thresh=0.001, label=""):
    correct = 0
    wrong = 0
    unknown = 0
    raga_stats = defaultdict(lambda: {"c": 0, "w": 0, "u": 0, "t": 0})
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
            pcd_score = np.dot(held["pcd"] * weights, raga_mean_pcd[r] * weights)
            dyad_score = (np.dot(held["up"], raga_mean_up[r]) +
                          np.dot(held["down"], raga_mean_down[r])) / 2
            scores[r] = pcd_w * pcd_score + dyad_w * dyad_score

        ranking = sorted(scores.items(), key=lambda x: -x[1])
        margin = ranking[0][1] - ranking[1][1] if len(ranking) >= 2 else 0

        if margin >= margin_thresh:
            pred = ranking[0][0]
        else:
            pred = "UNKNOWN"

        rs = raga_stats[held["raga"]]
        rs["t"] += 1
        if pred == "UNKNOWN":
            unknown += 1
            rs["u"] += 1
        elif pred == held["raga"]:
            correct += 1
            rs["c"] += 1
        else:
            wrong += 1
            rs["w"] += 1
            wrong_to[ranking[0][0]] += 1

    decided = correct + wrong
    acc = correct / decided if decided > 0 else 0

    print("{:40s} C={:2d} W={:2d} U={:2d} Dec={:2d} Acc={:.1f}%  Sinks: {}".format(
        label, correct, wrong, unknown, decided, acc * 100,
        ", ".join("{}={}".format(r, c) for r, c in sorted(wrong_to.items(), key=lambda x: -x[1])[:3])
    ))

    # Per-raga detail
    for r in sorted(raga_stats.keys()):
        s = raga_stats[r]
        d = s["c"] + s["w"]
        a = s["c"] / d * 100 if d > 0 else 0
        print("  {:20s} {:2d}c {:2d}w {:2d}u ({:.0f}%)".format(r, s["c"], s["w"], s["u"], a))
    print()
    return acc


# ============================================================
# BASELINE
# ============================================================
print("=" * 80)
run_loo(all_clips, 0.6, 0.4, 0.001, "A) Baseline 0.6/0.4 M=0.001")

# ============================================================
# B) DYAD WEIGHT VARIATIONS
# ============================================================
print("=" * 80)
run_loo(all_clips, 0.5, 0.5, 0.001, "B1) Equal 0.5/0.5 M=0.001")
run_loo(all_clips, 0.4, 0.6, 0.001, "B2) Dyad-heavy 0.4/0.6 M=0.001")
run_loo(all_clips, 0.7, 0.3, 0.001, "B3) PCD-heavy 0.7/0.3 M=0.001")

# ============================================================
# C) MARGIN THRESHOLD VARIATIONS
# ============================================================
print("=" * 80)
run_loo(all_clips, 0.6, 0.4, 0.0008, "C1) Lower margin 0.0008")
run_loo(all_clips, 0.6, 0.4, 0.0005, "C2) Lower margin 0.0005")
run_loo(all_clips, 0.6, 0.4, 0.002, "C3) Higher margin 0.002")

# ============================================================
# D) REMOVE WEAK MOHANAM CLIP (Shloka Sri Ramachandra, 936 frames)
# ============================================================
print("=" * 80)
filtered = [c for c in all_clips if "Shloka Sri Ramachandra" not in c["fname"]]
print("Clips after removing short Mohanam: {}".format(len(filtered)))
run_loo(filtered, 0.6, 0.4, 0.001, "D) No short clip, 0.6/0.4 M=0.001")

# ============================================================
# E) BEST COMBOS
# ============================================================
print("=" * 80)
run_loo(filtered, 0.5, 0.5, 0.001, "E1) No short + 0.5/0.5 M=0.001")
run_loo(filtered, 0.5, 0.5, 0.0008, "E2) No short + 0.5/0.5 M=0.0008")
run_loo(filtered, 0.4, 0.6, 0.001, "E3) No short + 0.4/0.6 M=0.001")
run_loo(filtered, 0.7, 0.3, 0.001, "E4) No short + 0.7/0.3 M=0.001")
run_loo(filtered, 0.6, 0.4, 0.0005, "E5) No short + 0.6/0.4 M=0.0005")
