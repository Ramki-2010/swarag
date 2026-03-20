"""
Phase 4 Production Test: Re-aggregate with 72 bins + score cached features.

Steps:
1. Re-aggregate all cached features with N_BINS=72 (saves new model files)
2. Load the 72-bin models
3. Score every cached clip using production scoring logic (IDF x Variance)
4. Compare with 36-bin production results

Uses cached cents_gated from features_v12/ — no audio re-extraction.
This gives production-equivalent results in ~2 minutes.
"""
import os, sys, numpy as np
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
N_BINS_NEW = 72
N_BINS_OLD = 36
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4
MARGIN_STRICT = 0.003
MIN_MARGIN_FINAL = 0.001

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
AGG_BASE = r"D:\Swaragam\pcd_results\aggregation\v1.2"


# ============================================================
# STEP 1: RE-AGGREGATE WITH NEW BIN COUNT
# ============================================================
def aggregate_with_bins(n_bins):
    """Rebuild raga models from cached features with given bin count."""
    print("  Aggregating with N_BINS={}...".format(n_bins))

    raga_pcds = {}
    raga_ups = {}
    raga_downs = {}

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
        raga = str(data["raga"])

        # PCD
        hist, _ = np.histogram(cents, bins=n_bins, range=(0, 1200))
        pcd = hist / (np.sum(hist) + EPS)

        # Dyads
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

        raga_pcds.setdefault(raga, []).append(pcd)
        raga_ups.setdefault(raga, []).append(mat_up.flatten())
        raga_downs.setdefault(raga, []).append(mat_down.flatten())

    # Build averaged models
    models = {}
    for raga in sorted(raga_pcds.keys()):
        models[raga] = {
            "pcd": np.mean(raga_pcds[raga], axis=0),
            "mean_up": np.mean(raga_ups[raga], axis=0),
            "mean_down": np.mean(raga_downs[raga], axis=0),
            "n": len(raga_pcds[raga]),
        }
        print("    {}: {} clips".format(raga, models[raga]["n"]))

    # Save to disk (same format as production aggregate_all_v12.py)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(AGG_BASE, "run_{}_{}bins".format(timestamp, n_bins))
    pcd_dir = os.path.join(run_dir, "pcd_stats")
    dyad_dir = os.path.join(run_dir, "dyad_stats")
    os.makedirs(pcd_dir, exist_ok=True)
    os.makedirs(dyad_dir, exist_ok=True)

    for raga, m in models.items():
        np.savez(os.path.join(pcd_dir, "{}_pcd_stats.npz".format(raga)),
                 mean_pcd=m["pcd"])
        np.savez(os.path.join(dyad_dir, "{}_dyad_stats.npz".format(raga)),
                 mean_up=m["mean_up"], mean_down=m["mean_down"])

    print("  Models saved to: {}".format(run_dir))
    return models, run_dir


# ============================================================
# STEP 2: COMPUTE IDF x VARIANCE WEIGHTS
# ============================================================
def compute_weights(models, n_bins):
    all_pcds = np.array([m["pcd"] for m in models.values()])
    threshold = 1.0 / n_bins
    doc_freq = np.sum(all_pcds > threshold, axis=0)
    idf = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std = np.std(all_pcds, axis=0)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * n_bins
    return weights


# ============================================================
# STEP 3: SCORE ALL CACHED CLIPS
# ============================================================
def score_all_clips(models, weights, n_bins):
    """Score every cached clip against models — production scoring logic."""

    raga_stats = {}
    all_results = []

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
        true_raga = str(data["raga"])

        # Recompute features with new bin count
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
        test_up = mat_up.flatten()
        test_down = mat_down.flatten()

        # IDF x Variance weighted scoring
        pcd_w = pcd * weights
        pcd_w = pcd_w / (np.sum(pcd_w) + EPS)

        scores = {}
        for raga, m in models.items():
            model_w = m["pcd"] * weights
            model_w = model_w / (np.sum(model_w) + EPS)
            pcd_sim = np.dot(pcd_w, model_w)
            dyad_sim = 0.5 * (np.dot(test_up, m["mean_up"]) +
                              np.dot(test_down, m["mean_down"]))
            scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0
        pred = ranked[0][0]

        if margin >= MARGIN_STRICT:
            tier = "HIGH"
        elif margin >= MIN_MARGIN_FINAL:
            tier = "MODERATE"
        else:
            tier = "UNKNOWN"
            pred = "UNKNOWN / LOW CONFIDENCE"

        s = raga_stats.setdefault(true_raga, {"t": 0, "c": 0, "w": 0, "u": 0})
        s["t"] += 1

        is_correct = (pred == true_raga)
        if is_correct and tier in ("HIGH", "MODERATE"):
            s["c"] += 1
            sym = "+"
        elif tier == "UNKNOWN":
            s["u"] += 1
            sym = "?"
        else:
            s["w"] += 1
            sym = "X"

        short_name = fname[:45]
        print("{} {:47} True={:20} Pred={:25} Tier={:8} Margin={:.4f}".format(
            sym, short_name, true_raga, pred, tier, margin))

        all_results.append({
            "file": fname, "true": true_raga, "pred": pred,
            "tier": tier, "margin": round(margin, 6)
        })

    return raga_stats, all_results


# ============================================================
# MAIN
# ============================================================
print("=" * 90)
print("PHASE 4 PRODUCTION TEST: 72-bin Models")
print("=" * 90)
print()

# Step 1: Aggregate
print("STEP 1: Re-aggregate with 72 bins")
models_72, run_dir_72 = aggregate_with_bins(72)
print()

# Step 2: Weights
print("STEP 2: Compute IDF x Variance weights")
weights_72 = compute_weights(models_72, 72)
print("  Weight range: {:.2f} - {:.2f}".format(weights_72.min(), weights_72.max()))
print()

# Step 3: Score
print("STEP 3: Score all 53 clips")
print("=" * 90)
stats_72, results_72 = score_all_clips(models_72, weights_72, 72)

# Summary
print()
print("=" * 90)
print("RESULTS: 72 bins (IDF x Variance)")
print("=" * 90)
total = sum(s["t"] for s in stats_72.values())
correct = sum(s["c"] for s in stats_72.values())
wrong = sum(s["w"] for s in stats_72.values())
unknown = sum(s["u"] for s in stats_72.values())
decided = total - unknown
acc = correct / decided if decided > 0 else 0

print()
print("  Total: {}  Correct: {}  Wrong: {}  Unknown: {} ({:.0f}%)".format(
    total, correct, wrong, unknown, 100 * unknown / total))
print("  Accuracy (decided): {:.0f}%".format(acc * 100))
print()

print("  Per-raga:")
for raga in sorted(stats_72.keys()):
    s = stats_72[raga]
    d = s["t"] - s["u"]
    a = s["c"] / d if d > 0 else 0
    print("    {:20} {:2d}/{:2d} correct  {:2d} wrong  {:2d} unk  ({:.0f}%)".format(
        raga, s["c"], s["t"], s["w"], s["u"], a * 100))

# Comparison with 36-bin production (from run_20260311_235231)
print()
print("=" * 90)
print("COMPARISON: 36 bins (current production) vs 72 bins")
print("=" * 90)
print()
print("  {:20} {:>12} {:>12} {:>8}".format("Metric", "36 bins", "72 bins", "Change"))
print("  " + "-" * 55)
print("  {:20} {:>12} {:>12} {:>+8}".format("Correct", 31, correct, correct - 31))
print("  {:20} {:>12} {:>12} {:>+8}".format("Wrong", 13, wrong, wrong - 13))
print("  {:20} {:>12} {:>12} {:>+8}".format("Unknown", 9, unknown, unknown - 9))
print("  {:20} {:>12} {:>12} {:>+8}".format("Acc (decided)", "70%",
      "{:.0f}%".format(acc * 100), ""))

# Per-raga comparison
prod_36 = {
    "Bhairavi": (3, 4, 4), "Kalyani": (9, 3, 2), "Kamboji": (3, 0, 0),
    "Mohanam": (2, 3, 1), "Shankarabharanam": (4, 3, 2), "Thodi": (10, 0, 0),
}
print()
print("  {:20} {:>10} {:>10}".format("Raga", "36-bin acc", "72-bin acc"))
print("  " + "-" * 42)
for raga in sorted(stats_72.keys()):
    c36, w36, u36 = prod_36[raga]
    d36 = c36 + w36
    a36 = c36 / d36 if d36 > 0 else 0
    s72 = stats_72[raga]
    d72 = s72["t"] - s72["u"]
    a72 = s72["c"] / d72 if d72 > 0 else 0
    arrow = ">>>" if a72 > a36 else ("===" if a72 == a36 else "<<<")
    print("  {:20} {:>9.0f}% {:>3} {:>6.0f}%".format(raga, a36 * 100, arrow, a72 * 100))

print()
print("72-bin models saved to: {}".format(run_dir_72))
print("Done.")
