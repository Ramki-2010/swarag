"""
SANDBOX: Phase 3 — Fix Thodi Sink (BUG-008)

Tests 3 approaches to stop Thodi from absorbing everything:
  A. Mean-subtracted PCD ("TF-IDF style") — remove common swara signal
  B. Cosine similarity — normalize by PCD magnitude
  C. IDF-weighted PCD — downweight bins shared by all ragas

Uses cached features from features_v12/ — no audio extraction needed.
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
# LOAD ALL FEATURES
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

        # PCD
        hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
        pcd = hist / (np.sum(hist) + EPS)

        # Dyads
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
    """Build raga models from clips."""
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


def score_cosine(pcd, up, down, models):
    """Method B: Cosine similarity (normalize by magnitude)."""
    scores = {}
    pcd_norm = np.linalg.norm(pcd) + EPS
    for raga, m in models.items():
        m_norm = np.linalg.norm(m["pcd"]) + EPS
        pcd_sim = np.dot(pcd, m["pcd"]) / (pcd_norm * m_norm)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def score_mean_sub(pcd, up, down, models, mean_pcd):
    """Method A: Mean-subtracted PCD (TF-IDF style)."""
    scores = {}
    test_sub = pcd - mean_pcd
    for raga, m in models.items():
        model_sub = m["pcd"] - mean_pcd
        pcd_sim = np.dot(test_sub, model_sub)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


def score_idf(pcd, up, down, models, idf_weights):
    """Method C: IDF-weighted PCD — downweight common bins."""
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
    
    # Per-raga breakdown
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
print("PHASE 3 SANDBOX: Thodi Sink Fix")
print("=" * 80)
print()

print("Loading features...")
clips = load_all_features()
print("  {} clips loaded".format(len(clips)))

models = build_models(clips)
print("  {} ragas: {}".format(len(models), ", ".join(sorted(models.keys()))))

# Compute global stats for methods A and C
all_model_pcds = np.array([m["pcd"] for m in models.values()])
mean_pcd = np.mean(all_model_pcds, axis=0)

# IDF: inverse document frequency — bins used by ALL ragas get low weight
# For each bin: how many ragas have significant mass (> 1/36 = 0.028)?
threshold = 1.0 / N_BINS
doc_freq = np.sum(all_model_pcds > threshold, axis=0)  # how many ragas use this bin
idf_weights = np.log(len(models) / (doc_freq + 1)) + 1  # IDF with smoothing

print()
print("Mean PCD top-5 bins: {}".format(np.argsort(mean_pcd)[-5:]))
print("IDF weights range: {:.2f} - {:.2f}".format(idf_weights.min(), idf_weights.max()))
print("  Highest IDF (most distinctive): bins {}".format(np.argsort(idf_weights)[-5:]))
print("  Lowest IDF (most common): bins {}".format(np.argsort(idf_weights)[:5]))

# ============================================================
# RUN ALL METHODS
# ============================================================
print()
print("=" * 80)
print("RESULTS COMPARISON")
print("=" * 80)
print()

print("Method A: Mean-subtracted PCD")
a_correct, a_wrong, a_thodi, a_wrongs = evaluate_method(
    clips, models, score_mean_sub, "Mean-Sub", mean_pcd=mean_pcd)

print()
print("Method B: Cosine similarity")
b_correct, b_wrong, b_thodi, b_wrongs = evaluate_method(
    clips, models, score_cosine, "Cosine")

print()
print("Method C: IDF-weighted PCD")
c_correct, c_wrong, c_thodi, c_wrongs = evaluate_method(
    clips, models, score_idf, "IDF-weighted", idf_weights=idf_weights)

print()
print("BASELINE (current production):")
base_correct, base_wrong, base_thodi, base_wrongs = evaluate_method(
    clips, models, score_baseline, "Baseline")

# ============================================================
# SUMMARY TABLE
# ============================================================
print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
total = len(clips)
print()
print("  {:20} {:>8} {:>8} {:>12} {:>10}".format(
    "Method", "Correct", "Wrong", "Thodi Sink", "Acc"))
print("  " + "-" * 60)
for label, cor, wr, ts in [
    ("Baseline", base_correct, base_wrong, base_thodi),
    ("A: Mean-Sub", a_correct, a_wrong, a_thodi),
    ("B: Cosine", b_correct, b_wrong, b_thodi),
    ("C: IDF-weighted", c_correct, c_wrong, c_thodi),
]:
    decided = total - (total - cor - wr)
    acc = cor / decided if decided > 0 else 0
    sink_pct = ts / wr if wr > 0 else 0
    print("  {:20} {:>8} {:>8} {:>8} ({:.0f}%) {:>8.0f}%".format(
        label, cor, wr, ts, sink_pct * 100, acc * 100))

# Show which wrongs each method FIXED vs baseline
print()
print("=" * 80)
print("FIXES vs BASELINE (wrongs that became correct)")
print("=" * 80)

base_wrong_set = set((w[0], w[1]) for w in base_wrongs)
for label, wrongs_list in [("A: Mean-Sub", a_wrongs), ("B: Cosine", b_wrongs), ("C: IDF", c_wrongs)]:
    wrong_set = set((w[0], w[1]) for w in wrongs_list)
    fixed = base_wrong_set - wrong_set
    broken = wrong_set - base_wrong_set
    print()
    print("  {} — Fixed {} baseline wrongs, broke {} new".format(label, len(fixed), len(broken)))
    if fixed:
        for f, r in sorted(fixed):
            print("    FIXED: {} ({})".format(f[:35], r))
    if broken:
        for f, r in sorted(broken):
            print("    BROKE: {} ({})".format(f[:35], r))

print()
print("Done.")
