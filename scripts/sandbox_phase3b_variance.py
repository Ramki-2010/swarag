"""
SANDBOX: Phase 3b — Variance Whitening vs IDF (BUG-008 Thodi Sink)

Adds Method D (variance whitening) and Method E (combined IDF+variance)
to the Phase 3 comparison. Reuses all infrastructure from Phase 3.

NO production files modified.
"""
import os, sys, numpy as np
sys.path.insert(0, ".")

# ============================================================
# CONFIG
# ============================================================
N_BINS = 36
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"

# ============================================================
# LOAD ALL FEATURES (same as Phase 3)
# ============================================================
def load_all_features():
    clips = []
    for fname in sorted(os.listdir(FEAT_DIR)):
        if not fname.endswith(".npz"):
            continue
        fpath = os.path.join(FEAT_DIR, fname)
        data = np.load(fpath, allow_pickle=True)
        if "feature_version" not in data or str(data["feature_version"]) != "v1.2":
            continue
        if float(data["gating_ratio"]) < 0.05:
            continue
        raga = str(data["raga"])
        cents = data["cents_gated"]
        if len(cents) < 200:
            continue

        hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
        pcd = hist / (np.sum(hist) + EPS)

        bins = np.linspace(0, 1200, N_BINS + 1)
        pitch_bins = np.digitize(cents, bins) - 1
        pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

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

        mat_up = np.zeros((N_BINS, N_BINS))
        mat_down = np.zeros((N_BINS, N_BINS))
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

        clips.append({
            "fname": fname[:45],
            "raga": raga,
            "pcd": pcd,
            "up": mat_up.flatten(),
            "down": mat_down.flatten(),
        })
    return clips


def build_models(clips):
    raga_data = {}
    for c in clips:
        raga_data.setdefault(c["raga"], []).append(c)
    models = {}
    for raga, rclips in raga_data.items():
        models[raga] = {
            "pcd": np.mean([c["pcd"] for c in rclips], axis=0),
            "up": np.mean([c["up"] for c in rclips], axis=0),
            "down": np.mean([c["down"] for c in rclips], axis=0),
            "n": len(rclips),
        }
    return models


# ============================================================
# SCORING METHODS
# ============================================================

def score_baseline(pcd, up, down, models):
    """Current production: raw dot-product."""
    scores = {}
    for raga, m in models.items():
        pcd_sim = np.dot(pcd, m["pcd"])
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def score_idf(pcd, up, down, models, idf_weights):
    """Method C: IDF-weighted PCD."""
    scores = {}
    test_w = pcd * idf_weights
    test_w = test_w / (np.sum(test_w) + EPS)
    for raga, m in models.items():
        model_w = m["pcd"] * idf_weights
        model_w = model_w / (np.sum(model_w) + EPS)
        pcd_sim = np.dot(test_w, model_w)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def score_variance_whiten(pcd, up, down, models, inv_std):
    """Method D: Variance whitening — divide each bin by its std across models."""
    scores = {}
    test_w = pcd * inv_std
    for raga, m in models.items():
        model_w = m["pcd"] * inv_std
        pcd_sim = np.dot(test_w, model_w)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def score_variance_whiten_normed(pcd, up, down, models, inv_std):
    """Method D2: Variance whitening + re-normalize to sum=1."""
    scores = {}
    test_w = pcd * inv_std
    test_w = test_w / (np.sum(test_w) + EPS)
    for raga, m in models.items():
        model_w = m["pcd"] * inv_std
        model_w = model_w / (np.sum(model_w) + EPS)
        pcd_sim = np.dot(test_w, model_w)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def score_idf_x_variance(pcd, up, down, models, combined_weights):
    """Method E: IDF * variance whitening combined."""
    scores = {}
    test_w = pcd * combined_weights
    test_w = test_w / (np.sum(test_w) + EPS)
    for raga, m in models.items():
        model_w = m["pcd"] * combined_weights
        model_w = model_w / (np.sum(model_w) + EPS)
        pcd_sim = np.dot(test_w, model_w)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def evaluate_method(clips, models, score_fn, label, **kwargs):
    """Run all clips through a scoring method and report results."""
    raga_stats = {}
    wrongs = []
    thodi_wrongs = 0

    for c in clips:
        scores = score_fn(c["pcd"], c["up"], c["down"], models, **kwargs)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0
        pred = ranked[0][0]

        tier = "HIGH" if margin >= 0.003 else ("MODERATE" if margin >= 0.001 else "UNKNOWN")

        true_raga = c["raga"]
        stats = raga_stats.setdefault(true_raga, {"total": 0, "correct": 0, "wrong": 0, "unknown": 0})
        stats["total"] += 1

        if pred == true_raga and tier in ("HIGH", "MODERATE"):
            stats["correct"] += 1
        elif tier == "UNKNOWN":
            stats["unknown"] += 1
        else:
            stats["wrong"] += 1
            if pred == "Thodi" and true_raga != "Thodi":
                thodi_wrongs += 1
            wrongs.append((c["fname"][:35], true_raga, pred, round(margin, 4)))

    total = sum(s["total"] for s in raga_stats.values())
    correct = sum(s["correct"] for s in raga_stats.values())
    wrong = sum(s["wrong"] for s in raga_stats.values())
    unknown = sum(s["unknown"] for s in raga_stats.values())
    decided = total - unknown
    acc = correct / decided if decided > 0 else 0

    print("  {:20} total={:2d}  correct={:2d}  wrong={:2d}  unk={:2d}  acc={:.0f}%  thodi_sink={}/{}".format(
        label, total, correct, wrong, unknown, acc * 100, thodi_wrongs, wrong))

    for raga in sorted(raga_stats.keys()):
        s = raga_stats[raga]
        r_decided = s["total"] - s["unknown"]
        r_acc = s["correct"] / r_decided if r_decided > 0 else 0
        print("    {:20} {:2d}/{:2d} correct  {:2d} wrong  {:2d} unk  ({:.0f}%)".format(
            raga, s["correct"], s["total"], s["wrong"], s["unknown"], r_acc * 100))

    return correct, wrong, thodi_wrongs, wrongs


# ============================================================
# MAIN
# ============================================================
print("=" * 80)
print("PHASE 3b SANDBOX: IDF vs Variance Whitening vs Combined")
print("=" * 80)
print()

print("Loading features...")
clips = load_all_features()
print("  {} clips loaded".format(len(clips)))

models = build_models(clips)
print("  {} ragas: {}".format(len(models), ", ".join(sorted(models.keys()))))

# ============================================================
# COMPUTE WEIGHTS
# ============================================================
all_model_pcds = np.array([m["pcd"] for m in models.values()])
mean_pcd = np.mean(all_model_pcds, axis=0)

# IDF weights (from Phase 3)
threshold = 1.0 / N_BINS
doc_freq = np.sum(all_model_pcds > threshold, axis=0)
idf_weights = np.log(len(models) / (doc_freq + 1)) + 1

# Variance whitening: 1/std per bin
bin_std = np.std(all_model_pcds, axis=0)
inv_std = 1.0 / (bin_std + EPS)

# Combined: IDF * inv_std
combined_weights = idf_weights * inv_std
combined_weights = combined_weights / (np.sum(combined_weights) + EPS) * N_BINS  # scale

print()
print("Variance per bin (top-5 highest = most distinctive):")
top5_var = np.argsort(bin_std)[-5:]
bot5_var = np.argsort(bin_std)[:5]
print("  Highest variance (distinctive): bins {} -> std={}".format(
    top5_var, np.round(bin_std[top5_var], 5)))
print("  Lowest variance (common):       bins {} -> std={}".format(
    bot5_var, np.round(bin_std[bot5_var], 5)))
print()
print("IDF weights range: {:.2f} - {:.2f}".format(idf_weights.min(), idf_weights.max()))
print("Inv-std range:     {:.1f} - {:.1f}".format(inv_std.min(), inv_std.max()))
print("Combined range:    {:.1f} - {:.1f}".format(combined_weights.min(), combined_weights.max()))

# ============================================================
# RUN ALL METHODS
# ============================================================
print()
print("=" * 80)
print("RESULTS COMPARISON (5 methods)")
print("=" * 80)

print()
print("BASELINE (current production):")
base_correct, base_wrong, base_thodi, base_wrongs = evaluate_method(
    clips, models, score_baseline, "Baseline")

print()
print("Method C: IDF-weighted PCD (Phase 3 winner):")
c_correct, c_wrong, c_thodi, c_wrongs = evaluate_method(
    clips, models, score_idf, "C: IDF", idf_weights=idf_weights)

print()
print("Method D: Variance whitening (raw):")
d_correct, d_wrong, d_thodi, d_wrongs = evaluate_method(
    clips, models, score_variance_whiten, "D: Var-whiten", inv_std=inv_std)

print()
print("Method D2: Variance whitening (normalized):")
d2_correct, d2_wrong, d2_thodi, d2_wrongs = evaluate_method(
    clips, models, score_variance_whiten_normed, "D2: Var-norm", inv_std=inv_std)

print()
print("Method E: IDF x Variance (combined):")
e_correct, e_wrong, e_thodi, e_wrongs = evaluate_method(
    clips, models, score_idf_x_variance, "E: IDF*Var", combined_weights=combined_weights)

# ============================================================
# SUMMARY TABLE
# ============================================================
print()
print("=" * 80)
print("FINAL COMPARISON TABLE")
print("=" * 80)
total = len(clips)
print()
print("  {:20} {:>8} {:>8} {:>12} {:>10}".format(
    "Method", "Correct", "Wrong", "Thodi Sink", "Acc"))
print("  " + "-" * 62)
for label, cor, wr, ts in [
    ("Baseline", base_correct, base_wrong, base_thodi),
    ("C: IDF", c_correct, c_wrong, c_thodi),
    ("D: Var-whiten", d_correct, d_wrong, d_thodi),
    ("D2: Var-norm", d2_correct, d2_wrong, d2_thodi),
    ("E: IDF*Var", e_correct, e_wrong, e_thodi),
]:
    decided = total - (total - cor - wr)
    acc = cor / decided if decided > 0 else 0
    sink_pct = ts / wr if wr > 0 else 0
    print("  {:20} {:>8} {:>8} {:>8} ({:.0f}%) {:>8.0f}%".format(
        label, cor, wr, ts, sink_pct * 100, acc * 100))

# Show fixes vs baseline for each method
print()
print("=" * 80)
print("NET FIXES vs BASELINE")
print("=" * 80)

base_wrong_set = set((w[0], w[1]) for w in base_wrongs)
for label, wrongs_list in [
    ("C: IDF", c_wrongs),
    ("D: Var-whiten", d_wrongs),
    ("D2: Var-norm", d2_wrongs),
    ("E: IDF*Var", e_wrongs),
]:
    wrong_set = set((w[0], w[1]) for w in wrongs_list)
    fixed = base_wrong_set - wrong_set
    broken = wrong_set - base_wrong_set
    net = len(fixed) - len(broken)
    print("  {:15} +{} fixed  -{} broke  net={:+d}".format(label, len(fixed), len(broken), net))

print()
print("Done.")
