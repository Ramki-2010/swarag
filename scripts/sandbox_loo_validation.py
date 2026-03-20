"""
Leave-One-Out Cross-Validation: 72 bins vs 36 bins

For each clip:
  1. Remove it from training set
  2. Build models from remaining clips
  3. Compute IDF x variance weights from those models
  4. Score the held-out clip
  5. Record result

This eliminates self-evaluation bias entirely.
Runs on cached features — no audio extraction needed (~2 min).
"""
import os, numpy as np

# ============================================================
# CONFIG
# ============================================================
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4
MARGIN_STRICT = 0.003
MIN_MARGIN_FINAL = 0.001

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


# ============================================================
# LOAD RAW CENTS
# ============================================================
def load_raw_clips():
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
        clips.append({
            "fname": fname[:45],
            "raga": str(data["raga"]),
            "cents": cents,
        })
    return clips


# ============================================================
# COMPUTE FEATURES
# ============================================================
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


# ============================================================
# LOO EVALUATION
# ============================================================
def leave_one_out(raw_clips, n_bins, label):
    """Leave-one-out cross-validation with IDF x variance scoring."""

    # Pre-compute features for all clips
    processed = []
    for c in raw_clips:
        pcd, up, down = compute_features(c["cents"], n_bins)
        processed.append({
            "fname": c["fname"],
            "raga": c["raga"],
            "pcd": pcd,
            "up": up,
            "down": down,
        })

    raga_stats = {}
    total_correct = 0
    total_wrong = 0
    total_unknown = 0
    thodi_sink = 0
    wrongs_list = []

    for i in range(len(processed)):
        held_out = processed[i]
        training = processed[:i] + processed[i + 1:]

        # Build models from training clips only
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

        # IDF x variance weights from TRAINING models only
        all_pcds = np.array([m["pcd"] for m in models.values()])
        threshold = 1.0 / n_bins
        doc_freq = np.sum(all_pcds > threshold, axis=0)
        idf = np.log(len(models) / (doc_freq + 1)) + 1
        bin_std = np.std(all_pcds, axis=0)
        weights = idf / (bin_std + EPS)
        weights = weights / (np.sum(weights) + EPS) * n_bins

        # Score held-out clip
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
            total_correct += 1
            sym = "+"
        elif tier == "UNK":
            s["u"] += 1
            total_unknown += 1
            sym = "?"
        else:
            s["w"] += 1
            total_wrong += 1
            if pred == "Thodi" and true_raga != "Thodi":
                thodi_sink += 1
            wrongs_list.append((held_out["fname"][:35], true_raga, pred, round(margin, 4)))
            sym = "X"

        print("  {} {:47} True={:15} Pred={:15} Tier={:4} Margin={:.4f}".format(
            sym, held_out["fname"][:47], true_raga, pred, tier, margin))

    decided = total_correct + total_wrong
    acc = total_correct / decided if decided > 0 else 0

    print()
    print("  {} LOO SUMMARY (N_BINS={})".format(label, n_bins))
    print("  " + "-" * 60)
    print("  Total: {}  Correct: {}  Wrong: {}  Unknown: {} ({:.0f}%)".format(
        len(processed), total_correct, total_wrong, total_unknown,
        100 * total_unknown / len(processed)))
    print("  Accuracy (decided): {:.1f}%".format(acc * 100))
    print("  Thodi sink: {}/{}".format(thodi_sink, total_wrong))
    print()
    print("  Per-raga:")
    for raga in sorted(raga_stats.keys()):
        s = raga_stats[raga]
        d = s["t"] - s["u"]
        a = s["c"] / d if d > 0 else 0
        print("    {:20} {:2d}/{:2d} correct  {:2d} wrong  {:2d} unk  ({:.0f}%)".format(
            raga, s["c"], s["t"], s["w"], s["u"], a * 100))

    if wrongs_list:
        print()
        print("  Wrong predictions:")
        for fname, true_r, pred_r, margin in wrongs_list:
            print("    {} ({}) -> {} (margin={})".format(fname, true_r, pred_r, margin))

    return total_correct, total_wrong, total_unknown, thodi_sink, acc


# ============================================================
# MAIN
# ============================================================
print("=" * 80)
print("LEAVE-ONE-OUT CROSS-VALIDATION")
print("True held-out accuracy — no self-evaluation bias")
print("=" * 80)
print()

raw_clips = load_raw_clips()
print("Loaded {} clips".format(len(raw_clips)))
print()

# Run LOO for both 36 and 72 bins
print("=" * 80)
print("36 BINS (current production baseline)")
print("=" * 80)
c36, w36, u36, ts36, acc36 = leave_one_out(raw_clips, 36, "36-bin")

print()
print("=" * 80)
print("72 BINS (proposed upgrade)")
print("=" * 80)
c72, w72, u72, ts72, acc72 = leave_one_out(raw_clips, 72, "72-bin")

# Final comparison
print()
print("=" * 80)
print("FINAL COMPARISON: TRUE HELD-OUT ACCURACY")
print("=" * 80)
print()
print("  {:20} {:>12} {:>12} {:>10}".format("Metric", "36 bins", "72 bins", "Change"))
print("  " + "-" * 58)
print("  {:20} {:>12} {:>12} {:>+10}".format("Correct", c36, c72, c72 - c36))
print("  {:20} {:>12} {:>12} {:>+10}".format("Wrong", w36, w72, w72 - w36))
print("  {:20} {:>12} {:>12} {:>+10}".format("Unknown", u36, u72, u72 - u36))
print("  {:20} {:>11.1f}% {:>11.1f}% {:>+9.1f}%".format(
    "Acc (decided)", acc36 * 100, acc72 * 100, (acc72 - acc36) * 100))
print("  {:20} {:>12} {:>12}".format(
    "Thodi sink", "{}/{}".format(ts36, w36), "{}/{}".format(ts72, w72)))
print()

if acc72 >= 0.75:
    print("  VERDICT: 72 bins PASSES the 75% threshold -> LOCK IT")
elif acc72 >= 0.70:
    print("  VERDICT: 72 bins marginal (70-75%) -> consider locking with caution")
else:
    print("  VERDICT: 72 bins FAILS (<70%) -> revert to 36 bins")

print()
print("Done.")
