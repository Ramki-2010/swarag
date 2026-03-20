"""
SANDBOX: Phase 4 — PCD Bin Resolution (36 vs 72 vs 120 bins)

Tests whether finer pitch resolution improves sibling raga separation.
36 bins = 33 cents/bin (shuddha Ma and prati Ma in same bin)
72 bins = 17 cents/bin (shuddha Ma and prati Ma in different bins)
120 bins = 10 cents/bin (near-gamaka resolution)

All use Method E (IDF x Variance) scoring from Phase 3.
Uses cached features from features_v12/ — no audio extraction needed.
NO production files modified.
"""
import os, sys, numpy as np
sys.path.insert(0, ".")

# ============================================================
# CONFIG
# ============================================================
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


# ============================================================
# LOAD RAW CENTS FROM FEATURES
# ============================================================
def load_raw_clips():
    """Load cents_gated + raga label from all feature files."""
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
# COMPUTE FEATURES WITH GIVEN N_BINS
# ============================================================
def compute_features(cents, n_bins):
    """Compute PCD + directional dyads from cents with given bin count."""
    # PCD
    hist, _ = np.histogram(cents, bins=n_bins, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)

    # Dyads with stable region detection
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
# BUILD MODELS + IDF x VARIANCE WEIGHTS
# ============================================================
def build_models_and_weights(processed_clips):
    """Build raga models and IDF x variance weights."""
    raga_data = {}
    for c in processed_clips:
        raga_data.setdefault(c["raga"], []).append(c)

    models = {}
    for raga, rclips in raga_data.items():
        models[raga] = {
            "pcd": np.mean([c["pcd"] for c in rclips], axis=0),
            "up": np.mean([c["up"] for c in rclips], axis=0),
            "down": np.mean([c["down"] for c in rclips], axis=0),
            "n": len(rclips),
        }

    # IDF x Variance weights
    n_bins = len(list(models.values())[0]["pcd"])
    all_pcds = np.array([m["pcd"] for m in models.values()])
    threshold = 1.0 / n_bins
    doc_freq = np.sum(all_pcds > threshold, axis=0)
    idf = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std = np.std(all_pcds, axis=0)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * n_bins

    return models, weights


# ============================================================
# SCORING (Method E)
# ============================================================
def score_clip(pcd, up, down, models, weights):
    """Score one clip against all models with IDF x variance weighting."""
    pcd_w = pcd * weights
    pcd_w = pcd_w / (np.sum(pcd_w) + EPS)

    scores = {}
    for raga, m in models.items():
        model_w = m["pcd"] * weights
        model_w = model_w / (np.sum(model_w) + EPS)
        pcd_sim = np.dot(pcd_w, model_w)
        dyad_sim = 0.5 * (np.dot(up, m["up"]) + np.dot(down, m["down"]))
        scores[raga] = PCD_W * pcd_sim + DYAD_W * dyad_sim
    return scores


# ============================================================
# EVALUATE
# ============================================================
def evaluate(raw_clips, n_bins, label):
    """Full evaluation pipeline for a given bin count."""

    # Process all clips with this bin count
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

    models, weights = build_models_and_weights(processed)

    raga_stats = {}
    wrongs = []
    thodi_wrongs = 0

    for c in processed:
        scores = score_clip(c["pcd"], c["up"], c["down"], models, weights)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0
        pred = ranked[0][0]
        tier = "HIGH" if margin >= 0.003 else ("MOD" if margin >= 0.001 else "UNK")

        true_raga = c["raga"]
        s = raga_stats.setdefault(true_raga, {"t": 0, "c": 0, "w": 0, "u": 0})
        s["t"] += 1

        if pred == true_raga and tier in ("HIGH", "MOD"):
            s["c"] += 1
        elif tier == "UNK":
            s["u"] += 1
        else:
            s["w"] += 1
            if pred == "Thodi" and true_raga != "Thodi":
                thodi_wrongs += 1
            wrongs.append((c["fname"][:35], true_raga, pred, round(margin, 4)))

    total = sum(s["t"] for s in raga_stats.values())
    correct = sum(s["c"] for s in raga_stats.values())
    wrong = sum(s["w"] for s in raga_stats.values())
    unknown = sum(s["u"] for s in raga_stats.values())
    decided = total - unknown
    acc = correct / decided if decided > 0 else 0

    print("  {:12} bins={:3d}  correct={:2d}  wrong={:2d}  unk={:2d}  acc={:.0f}%  thodi_sink={}/{}".format(
        label, n_bins, correct, wrong, unknown, acc * 100, thodi_wrongs, wrong))

    for raga in sorted(raga_stats.keys()):
        s = raga_stats[raga]
        d = s["t"] - s["u"]
        a = s["c"] / d if d > 0 else 0
        print("    {:20} {:2d}/{:2d} correct  {:2d} wrong  {:2d} unk  ({:.0f}%)".format(
            raga, s["c"], s["t"], s["w"], s["u"], a * 100))

    return correct, wrong, unknown, thodi_wrongs, wrongs


# ============================================================
# MAIN
# ============================================================
print("=" * 80)
print("PHASE 4 SANDBOX: PCD Bin Resolution")
print("=" * 80)
print()

print("Loading raw features...")
raw_clips = load_raw_clips()
print("  {} clips loaded".format(len(raw_clips)))
print()

# Musically important reference points (in cents from Sa):
print("Microtonal reference:")
print("  Shuddha Ma (Ma1): ~498 cents")
print("  Prati Ma (Ma2):   ~590 cents")
print("  Difference:        92 cents")
print()
print("  At 36 bins (33 c/bin): Ma1=bin 15, Ma2=bin 17-18  (2-3 bins apart)")
print("  At 72 bins (17 c/bin): Ma1=bin 29, Ma2=bin 35     (6 bins apart)")
print("  At 120 bins (10 c/bin): Ma1=bin 50, Ma2=bin 59    (9 bins apart)")
print()

bin_configs = [36, 48, 60, 72, 96, 120]

results = {}
for n_bins in bin_configs:
    print("-" * 80)
    c, w, u, ts, wrongs = evaluate(raw_clips, n_bins, "N={}".format(n_bins))
    results[n_bins] = {"correct": c, "wrong": w, "unknown": u, "thodi_sink": ts, "wrongs": wrongs}
    print()

# ============================================================
# SUMMARY
# ============================================================
print("=" * 80)
print("FINAL COMPARISON TABLE")
print("=" * 80)
print()
print("  {:>6} {:>8} {:>8} {:>6} {:>12} {:>8}".format(
    "Bins", "Correct", "Wrong", "Unk", "Thodi Sink", "Acc"))
print("  " + "-" * 55)

total = len(raw_clips)
for n_bins in bin_configs:
    r = results[n_bins]
    decided = total - r["unknown"]
    acc = r["correct"] / decided if decided > 0 else 0
    sink_pct = r["thodi_sink"] / r["wrong"] if r["wrong"] > 0 else 0
    marker = " <-- current" if n_bins == 36 else ""
    print("  {:>6} {:>8} {:>8} {:>6} {:>8} ({:.0f}%) {:>7.0f}%{}".format(
        n_bins, r["correct"], r["wrong"], r["unknown"],
        r["thodi_sink"], sink_pct * 100, acc * 100, marker))

# Show what the best config FIXED vs 36 bins
best_bins = max(results.keys(), key=lambda k: results[k]["correct"])
best = results[best_bins]
base = results[36]

print()
print("=" * 80)
print("BEST: {} bins vs 36 bins (current)".format(best_bins))
print("=" * 80)

base_wrongs = set((w[0], w[1]) for w in base["wrongs"])
best_wrongs = set((w[0], w[1]) for w in best["wrongs"])
fixed = base_wrongs - best_wrongs
broken = best_wrongs - base_wrongs

print("  Fixed {} wrongs, broke {} new (net {:+d})".format(
    len(fixed), len(broken), len(fixed) - len(broken)))
if fixed:
    print("  FIXED:")
    for f, r in sorted(fixed):
        print("    {} ({})".format(f, r))
if broken:
    print("  BROKE:")
    for f, r in sorted(broken):
        print("    {} ({})".format(f, r))

print()
print("Done.")
