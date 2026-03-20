"""
LOO cross-validation on 9 ragas / 81 clips with 72-bin IDF x Variance.
Compares: old (6 ragas/53 clips) vs new (9 ragas/81 clips).
"""
import os, numpy as np

N_BINS = 72
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4
MARGIN_STRICT = 0.003
MIN_MARGIN_FINAL = 0.001

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


def load_clips():
    clips = []
    for fname in sorted(os.listdir(FEAT_DIR)):
        if not fname.endswith(".npz"):
            continue
        data = np.load(os.path.join(FEAT_DIR, fname), allow_pickle=True)
        if "feature_version" not in data or str(data["feature_version"]) != "v1.2":
            continue
        if float(data["gating_ratio"]) < 0.05:
            continue
        cents = data["cents_gated"]
        if len(cents) < 200:
            continue
        clips.append({"fname": fname[:50], "raga": str(data["raga"]), "cents": cents})
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
    wrongs = []

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
            sym = "+"
        elif tier == "UNK":
            s["u"] += 1
            total_u += 1
            sym = "?"
        else:
            s["w"] += 1
            total_w += 1
            wrongs.append((held_out["fname"][:40], true_raga, pred, round(margin, 4)))
            sym = "X"

        print("  {} {:50} True={:18} Pred={:18} Tier={:4} M={:.4f}".format(
            sym, held_out["fname"][:50], true_raga, pred, tier, margin))

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

    if wrongs:
        print()
        print("  Wrongs:")
        for fname, true_r, pred_r, margin in wrongs:
            print("    {} ({}) -> {} (m={})".format(fname, true_r, pred_r, margin))

    return total_c, total_w, total_u, acc, raga_stats


# ============================================================
# MAIN
# ============================================================
print("=" * 80)
print("LOO CROSS-VALIDATION: 9 Ragas / 81 Clips / 72 Bins")
print("=" * 80)
print()

raw_clips = load_clips()
print("Loaded {} clips".format(len(raw_clips)))

# Count per raga
raga_counts = {}
for c in raw_clips:
    raga_counts[c["raga"]] = raga_counts.get(c["raga"], 0) + 1
for raga in sorted(raga_counts.keys()):
    print("  {:20} {:3d} clips".format(raga, raga_counts[raga]))
print()

cN, wN, uN, accN, statsN = loo_eval(raw_clips, N_BINS, "9-RAGA LOO")

# Compare with old results
print()
print("=" * 80)
print("COMPARISON: Old (6 ragas/53 clips) vs New (9 ragas/81 clips)")
print("=" * 80)
print()
print("  {:25} {:>12} {:>12}".format("Metric", "Old (6r/53c)", "New (9r/81c)"))
print("  " + "-" * 50)
print("  {:25} {:>12} {:>12}".format("Correct", 22, cN))
print("  {:25} {:>12} {:>12}".format("Wrong", 6, wN))
print("  {:25} {:>12} {:>12}".format("Unknown", 25, uN))
print("  {:25} {:>11.1f}% {:>11.1f}%".format("Acc (decided)", 78.6, accN * 100))
print("  {:25} {:>12} {:>12}".format("Ragas", 6, len(raga_counts)))
print("  {:25} {:>12} {:>12}".format("Total clips", 53, len(raw_clips)))
print()

if accN * 100 > 78.6:
    print("  VERDICT: NEW SYSTEM IS BETTER")
elif accN * 100 >= 75.0:
    print("  VERDICT: NEW SYSTEM IS COMPARABLE (more ragas, maintained accuracy)")
else:
    print("  VERDICT: ACCURACY DROPPED - investigate per-raga")

print()
print("Done.")
