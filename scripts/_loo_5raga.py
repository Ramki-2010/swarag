"""
Proper LOO with PCD + Dyads (IDF x Variance), matching production scoring.
Tests 5-raga model (Kamboji excluded after Harikambhoji cleanup).
"""
import os, numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
N_BINS = 72
ALPHA = 0.01
EPS = 1e-8
MIN_STABLE = 5
PCD_W = 0.6
DYAD_W = 0.4
MARGIN_THRESH = 0.001

def extract_features(data):
    cents = data["cents_gated"]
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)

    bins = np.floor(cents / (1200.0 / N_BINS)).astype(int)
    bins = np.clip(bins, 0, N_BINS - 1)

    up = np.zeros((N_BINS, N_BINS))
    down = np.zeros((N_BINS, N_BINS))
    stable_count = 0

    i = 0
    while i < len(bins):
        j = i + 1
        while j < len(bins) and bins[j] == bins[i]:
            j += 1
        run_len = j - i
        if run_len >= MIN_STABLE and i > 0:
            stable_count += 1
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

# Load all clips
clips = []
modeled = {"Bhairavi", "Kalyani", "Mohanam", "Shankarabharanam", "Thodi"}

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
    if raga not in modeled:
        continue
    cents = d["cents_gated"]
    if len(cents) < 200:
        continue

    pcd, up, down = extract_features(d)
    clips.append({"fname": f, "raga": raga, "pcd": pcd, "up": up, "down": down})

print("Clips: {}".format(len(clips)))
for r in sorted(modeled):
    print("  {:20s} {}".format(r, sum(1 for c in clips if c["raga"] == r)))

# LOO
correct = 0
wrong = 0
unknown = 0
raga_stats = defaultdict(lambda: {"c": 0, "w": 0, "u": 0, "t": 0})
wrong_details = []

for i, held in enumerate(clips):
    train = [c for j, c in enumerate(clips) if j != i]

    # Build models
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

    # IDF x Variance weights
    all_pcds = np.array(list(raga_mean_pcd.values()))
    doc_freq = np.sum(all_pcds > 0.001, axis=0) + 1
    idf = np.log(len(raga_mean_pcd) / doc_freq)
    std = np.std(all_pcds, axis=0)
    weights = idf / (std + EPS)
    weights = weights / (np.sum(weights) + EPS) * N_BINS

    # Score each raga
    scores = {}
    for r in raga_mean_pcd:
        pcd_score = np.dot(held["pcd"] * weights, raga_mean_pcd[r] * weights)
        dyad_score = (np.dot(held["up"], raga_mean_up[r]) + np.dot(held["down"], raga_mean_down[r])) / 2
        scores[r] = PCD_W * pcd_score + DYAD_W * dyad_score

    ranking = sorted(scores.items(), key=lambda x: -x[1])
    margin = ranking[0][1] - ranking[1][1] if len(ranking) >= 2 else 0

    if margin >= MARGIN_THRESH:
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
        wrong_details.append((held["fname"][:45], held["raga"], pred, round(margin, 5)))

decided = correct + wrong
acc = correct / decided if decided > 0 else 0

print()
print("LOO Results (5 ragas, {} clips, PCD+Dyads):".format(len(clips)))
print("  Correct: {}  Wrong: {}  Unknown: {}  Decided: {}".format(correct, wrong, unknown, decided))
print("  Accuracy (decided): {:.1f}%".format(acc * 100))
print()
print("Per-raga:")
for r in sorted(raga_stats.keys()):
    s = raga_stats[r]
    d = s["c"] + s["w"]
    a = s["c"] / d * 100 if d > 0 else 0
    print("  {:20s} {:2d}/{:2d} correct  {:2d} wrong  {:2d} unk  ({:.0f}%)".format(
        r, s["c"], s["t"], s["w"], s["u"], a))

if wrong_details:
    print()
    print("Wrong predictions:")
    for fname, true, pred, m in wrong_details:
        print("  {} true={} pred={} margin={:.5f}".format(fname, true, pred, m))
