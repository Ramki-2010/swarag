"""
Diagnostic: Compare LOO on 6 original ragas vs all 9.
Tests whether the accuracy drop is from thin new ragas poisoning IDF weights.
"""
import os, numpy as np
from collections import defaultdict

N_BINS = 72
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4
MARGIN_STRICT = 0.003
MIN_MARGIN_FINAL = 0.001

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
ORIGINAL_6 = {"Bhairavi", "Kalyani", "Shankarabharanam", "Thodi", "Mohanam", "Kamboji"}


def load_clips(raga_filter=None):
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
        cents = data["cents_gated"]
        if len(cents) < 200:
            continue
        raga = str(data["raga"])
        if raga_filter and raga not in raga_filter:
            continue
        clips.append({"fname": fname[:50], "raga": raga, "cents": cents})
    return clips


def compute_features(cents, n_bins):
    hist, _ = np.histogram(cents, bins=n_bins, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)

    bin_edges = np.linspace(0, 1200, n_bins + 1)
    pitch_bins = np.digitize(cents, bin_edges) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < n_bins)]

    stable_bins = []
    current = pitch_bins[0]
    count = 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current = b
            count = 1
    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)

    mat_up = np.zeros((n_bins, n_bins))
    mat_down = np.zeros((n_bins, n_bins))
    for i in range(len(stable_bins) - 1):
        frm, to = stable_bins[i], stable_bins[i + 1]
        if to > frm:
            mat_up[frm, to] += 1
        elif to < frm:
            mat_down[frm, to] += 1
    mat_up += ALPHA
    mat_down += ALPHA
    mat_up /= (np.sum(mat_up) + EPS)
    mat_down /= (np.sum(mat_down) + EPS)
    return pcd, mat_up.flatten(), mat_down.flatten()


def compute_idf_var_weights(models, n_bins):
    all_pcds = np.array([m["pcd"] for m in models.values()])
    threshold = 1.0 / n_bins
    doc_freq = np.sum(all_pcds > threshold, axis=0)
    idf = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std = np.std(all_pcds, axis=0)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * n_bins
    return weights


def loo_eval(raw_clips, n_bins, label):
    processed = []
    for c in raw_clips:
        pcd, up, down = compute_features(c["cents"], n_bins)
        processed.append({"fname": c["fname"], "raga": c["raga"],
                          "pcd": pcd, "up": up, "down": down})

    raga_stats = {}
    total_c = total_w = total_u = 0
    wrongs_by_pred = defaultdict(int)

    for i in range(len(processed)):
        held_out = processed[i]
        training = processed[:i] + processed[i + 1:]

        raga_data = {}
        for c in training:
            raga_data.setdefault(c["raga"], []).append(c)

        models = {}
        for raga, rclips in raga_data.items():
            models[raga] = {
                "pcd": np.mean([c["pcd"] for c in rclips], axis=0),
                "up": np.mean([c["up"] for c in rclips], axis=0),
                "down": np.mean([c["down"] for c in rclips], axis=0),
            }

        weights = compute_idf_var_weights(models, n_bins)

        pcd_w = held_out["pcd"] * weights
        pcd_w = pcd_w / (np.sum(pcd_w) + EPS)

        scores = {}
        for raga, m in models.items():
            model_w = m["pcd"] * weights
            model_w = model_w / (np.sum(model_w) + EPS)
            pcd_sim = np.dot(pcd_w, model_w)
            dyad_sim = 0.5 * (np.dot(held_out["up"], m["up"]) +
                              np.dot(held_out["down"], m["down"]))
            scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0
        pred = ranked[0][0]

        if margin >= MARGIN_STRICT:
            tier = "HIGH"
        elif margin >= MIN_MARGIN_FINAL:
            tier = "MOD"
        else:
            tier = "UNK"
            pred = "UNKNOWN"

        true_raga = held_out["raga"]
        s = raga_stats.setdefault(true_raga, {"t": 0, "c": 0, "w": 0, "u": 0})
        s["t"] += 1

        if pred == true_raga and tier in ("HIGH", "MOD"):
            s["c"] += 1
            total_c += 1
        elif tier == "UNK":
            s["u"] += 1
            total_u += 1
        else:
            s["w"] += 1
            total_w += 1
            wrongs_by_pred[pred] += 1

    decided = total_c + total_w
    acc = total_c / decided if decided > 0 else 0

    print()
    print("  {} LOO RESULTS".format(label))
    print("  " + "-" * 65)
    print("  Total: {}  Correct: {}  Wrong: {}  Unknown: {} ({:.0f}%)".format(
        len(processed), total_c, total_w, total_u,
        100 * total_u / len(processed)))
    print("  Accuracy (decided): {:.1f}%".format(acc * 100))
    print()
    print("  Per-raga:")
    for raga in sorted(raga_stats.keys()):
        s = raga_stats[raga]
        d = s["t"] - s["u"]
        a = s["c"] / d if d > 0 else 0
        print("    {:20} {:2d}/{:2d} correct  {:2d} wrong  {:2d} unk  ({:.0f}%)".format(
            raga, s["c"], s["t"], s["w"], s["u"], a * 100))

    if wrongs_by_pred:
        print()
        print("  Wrong predictions go to:")
        for pred_raga, count in sorted(wrongs_by_pred.items(), key=lambda x: -x[1]):
            print("    {:20} {} wrongs".format(pred_raga, count))

    return total_c, total_w, total_u, acc


print("=" * 80)
print("DIAGNOSTIC: 6 Original Ragas vs All 9 (LOO)")
print("=" * 80)

# Test 1: Original 6 ragas (with updated clip counts)
print("\nTEST 1: Original 6 ragas (updated clips: Kamboji 5, Mohanam 11)")
clips_6 = load_clips(ORIGINAL_6)
print("Loaded {} clips".format(len(clips_6)))
raga_counts_6 = defaultdict(int)
for c in clips_6:
    raga_counts_6[c["raga"]] += 1
for raga in sorted(raga_counts_6.keys()):
    print("  {:20} {:3d}".format(raga, raga_counts_6[raga]))

c6, w6, u6, a6 = loo_eval(clips_6, N_BINS, "6-RAGA (updated clips)")

# Test 2: All 9 ragas
print("\n\nTEST 2: All 9 ragas")
clips_9 = load_clips()
print("Loaded {} clips".format(len(clips_9)))
raga_counts_9 = defaultdict(int)
for c in clips_9:
    raga_counts_9[c["raga"]] += 1
for raga in sorted(raga_counts_9.keys()):
    print("  {:20} {:3d}".format(raga, raga_counts_9[raga]))

c9, w9, u9, a9 = loo_eval(clips_9, N_BINS, "9-RAGA (all)")

# Comparison
print()
print("=" * 80)
print("COMPARISON")
print("=" * 80)
print("  {:25} {:>12} {:>12} {:>12}".format("Metric", "Old 6r/53c", "New 6r/64c", "New 9r/68c"))
print("  " + "-" * 65)
print("  {:25} {:>12} {:>12} {:>12}".format("Correct", 22, c6, c9))
print("  {:25} {:>12} {:>12} {:>12}".format("Wrong", 6, w6, w9))
print("  {:25} {:>12} {:>12} {:>12}".format("Unknown", 25, u6, u9))
print("  {:25} {:>11.1f}% {:>11.1f}% {:>11.1f}%".format("Acc (decided)", 78.6, a6 * 100, a9 * 100))

print()
if a6 * 100 >= 75:
    print("  6-raga with expanded data: GOOD (maintained accuracy)")
else:
    print("  6-raga with expanded data: DEGRADED (investigate)")

if a9 * 100 >= 75:
    print("  9-raga: GOOD")
elif a9 * 100 < a6 * 100 - 10:
    print("  9-raga: SINK PROBLEM from thin new ragas")
else:
    print("  9-raga: needs investigation")

print("\nDone.")
