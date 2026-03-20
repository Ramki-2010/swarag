"""
SANDBOX: Hubness Correction (centered) — LOO validation

Tests hubness correction on top of IDF x Variance + 72 bins.
Uses leave-one-out for true held-out accuracy.

Method: score = raw_score - avg_sim[raga] + global_mean
Where avg_sim = mean MODEL-to-MODEL similarity (not query).

Compares:
  A. 72-bin IDF x Variance (current, no hubness)
  B. 72-bin IDF x Variance + hubness correction (centered)

NO production files modified.
"""
import os, numpy as np

# ============================================================
# CONFIG
# ============================================================
N_BINS = 72
MIN_STABLE_FRAMES = 5
ALPHA = 0.01
EPS = 1e-8
PCD_W = 0.6
DYAD_W = 0.4
MARGIN_STRICT = 0.003
MIN_MARGIN_FINAL = 0.001

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


# ============================================================
# LOAD + COMPUTE FEATURES
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
# IDF x VARIANCE WEIGHTS
# ============================================================
def compute_idf_var_weights(models, n_bins):
    all_pcds = np.array([m["pcd"] for m in models.values()])
    threshold = 1.0 / n_bins
    doc_freq = np.sum(all_pcds > threshold, axis=0)
    idf = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std = np.std(all_pcds, axis=0)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * n_bins
    return weights


# ============================================================
# HUBNESS CORRECTION (centered, model-to-model only)
# ============================================================
def compute_hubness(models, pcd_weights):
    """Compute avg_sim and global_mean from model-to-model similarities."""

    # Weighted PCDs for all models
    weighted_pcds = {}
    for raga, m in models.items():
        w = m["pcd"] * pcd_weights
        w = w / (np.sum(w) + EPS)
        weighted_pcds[raga] = w

    avg_sim = {}
    raga_list = list(models.keys())

    for raga_i in raga_list:
        sims = []
        for raga_j in raga_list:
            if raga_i == raga_j:
                continue
            pcd_sim = np.dot(weighted_pcds[raga_i], weighted_pcds[raga_j])
            up_sim = np.dot(models[raga_i]["up"], models[raga_j]["up"])
            down_sim = np.dot(models[raga_i]["down"], models[raga_j]["down"])
            dyad_sim = 0.5 * (up_sim + down_sim)
            sim = PCD_W * pcd_sim + DYAD_W * dyad_sim
            sims.append(sim)
        avg_sim[raga_i] = np.mean(sims)

    global_mean = np.mean(list(avg_sim.values()))
    return avg_sim, global_mean


# ============================================================
# LOO EVALUATION
# ============================================================
def loo_eval(raw_clips, n_bins, use_hubness, label):
    """Leave-one-out with optional hubness correction."""

    # Pre-compute features
    processed = []
    for c in raw_clips:
        pcd, up, down = compute_features(c["cents"], n_bins)
        processed.append({
            "fname": c["fname"], "raga": c["raga"],
            "pcd": pcd, "up": up, "down": down,
        })

    raga_stats = {}
    total_c = 0
    total_w = 0
    total_u = 0
    thodi_sink = 0
    wrongs = []

    for i in range(len(processed)):
        held_out = processed[i]
        training = processed[:i] + processed[i + 1:]

        # Build models from training only
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

        # IDF x variance weights from training models
        weights = compute_idf_var_weights(models, n_bins)

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

        # Apply hubness correction if enabled
        if use_hubness:
            avg_sim, global_mean = compute_hubness(models, weights)
            for raga in scores:
                scores[raga] = scores[raga] - avg_sim[raga] + global_mean

        # Margin gating
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
            if pred == "Thodi" and true_raga != "Thodi":
                thodi_sink += 1
            wrongs.append((held_out["fname"][:35], true_raga, pred, round(margin, 4)))
            sym = "X"

        print("  {} {:47} True={:15} Pred={:15} Tier={:4} Margin={:.4f}".format(
            sym, held_out["fname"][:47], true_raga, pred, tier, margin))

    decided = total_c + total_w
    acc = total_c / decided if decided > 0 else 0

    print()
    print("  {} LOO RESULTS (N_BINS={}, hubness={})".format(label, n_bins, use_hubness))
    print("  " + "-" * 65)
    print("  Total: {}  Correct: {}  Wrong: {}  Unknown: {} ({:.0f}%)".format(
        len(processed), total_c, total_w, total_u,
        100 * total_u / len(processed)))
    print("  Accuracy (decided): {:.1f}%".format(acc * 100))
    print("  Thodi sink: {}/{}".format(thodi_sink, total_w))
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
            print("    {} ({}) -> {} (margin={})".format(fname, true_r, pred_r, margin))

    return total_c, total_w, total_u, thodi_sink, acc, raga_stats


# ============================================================
# ALSO: Show hubness values from full model (diagnostic)
# ============================================================
def show_hubness_diagnostic(raw_clips, n_bins):
    """Show which ragas are hubs using the full model set."""
    processed = []
    for c in raw_clips:
        pcd, up, down = compute_features(c["cents"], n_bins)
        processed.append({"raga": c["raga"], "pcd": pcd, "up": up, "down": down})

    raga_data = {}
    for c in processed:
        raga_data.setdefault(c["raga"], []).append(c)

    models = {}
    for raga, rclips in raga_data.items():
        models[raga] = {
            "pcd": np.mean([c["pcd"] for c in rclips], axis=0),
            "up": np.mean([c["up"] for c in rclips], axis=0),
            "down": np.mean([c["down"] for c in rclips], axis=0),
        }

    weights = compute_idf_var_weights(models, n_bins)
    avg_sim, global_mean = compute_hubness(models, weights)

    print("  Hubness Diagnostic (72 bins, IDF x Variance)")
    print("  " + "-" * 55)
    print("  Global mean similarity: {:.6f}".format(global_mean))
    print()
    for raga in sorted(avg_sim.keys(), key=lambda r: avg_sim[r], reverse=True):
        bias = avg_sim[raga] - global_mean
        bar = "#" * int(abs(bias) * 20000)
        direction = "+" if bias > 0 else "-"
        tag = "HUB" if bias > 0.0003 else ("low" if bias < -0.0003 else "ok")
        print("  {:20} avg_sim={:.6f}  bias={:+.6f}  [{:3}] {}{}".format(
            raga, avg_sim[raga], bias, tag, direction, bar))


# ============================================================
# MAIN
# ============================================================
print("=" * 80)
print("SANDBOX: Hubness Correction (LOO Validation)")
print("=" * 80)
print()

raw_clips = load_raw_clips()
print("Loaded {} clips".format(len(raw_clips)))
print()

# Diagnostic: which ragas are hubs?
print("=" * 80)
print("HUBNESS DIAGNOSTIC")
print("=" * 80)
show_hubness_diagnostic(raw_clips, N_BINS)
print()

# A: Current system (72 bins, IDF x Variance, NO hubness)
print("=" * 80)
print("A: 72-bin IDF x Variance (NO hubness) — LOO")
print("=" * 80)
cA, wA, uA, tsA, accA, statsA = loo_eval(raw_clips, N_BINS, False, "A")

print()

# B: With hubness correction
print("=" * 80)
print("B: 72-bin IDF x Variance + HUBNESS correction — LOO")
print("=" * 80)
cB, wB, uB, tsB, accB, statsB = loo_eval(raw_clips, N_BINS, True, "B")

# ============================================================
# FINAL COMPARISON
# ============================================================
print()
print("=" * 80)
print("FINAL COMPARISON (LOO — true held-out accuracy)")
print("=" * 80)
print()
print("  {:25} {:>12} {:>12} {:>10}".format("Metric", "No Hubness", "+ Hubness", "Change"))
print("  " + "-" * 60)
print("  {:25} {:>12} {:>12} {:>+10}".format("Correct", cA, cB, cB - cA))
print("  {:25} {:>12} {:>12} {:>+10}".format("Wrong", wA, wB, wB - wA))
print("  {:25} {:>12} {:>12} {:>+10}".format("Unknown", uA, uB, uB - uA))
print("  {:25} {:>11.1f}% {:>11.1f}% {:>+9.1f}%".format(
    "Acc (decided)", accA * 100, accB * 100, (accB - accA) * 100))
print("  {:25} {:>12} {:>12}".format(
    "Thodi sink", "{}/{}".format(tsA, wA), "{}/{}".format(tsB, wB)))

print()
# Per-raga comparison
print("  {:20} {:>10} {:>10} {:>8}".format("Raga", "No Hub", "+ Hub", "Change"))
print("  " + "-" * 50)
for raga in sorted(statsA.keys()):
    sA = statsA[raga]
    sB = statsB[raga]
    dA = sA["t"] - sA["u"]
    dB = sB["t"] - sB["u"]
    aA = sA["c"] / dA if dA > 0 else 0
    aB = sB["c"] / dB if dB > 0 else 0
    change = aB - aA
    arrow = ">>>" if change > 0.05 else ("<<<" if change < -0.05 else "===")
    print("  {:20} {:>9.0f}% {:>9.0f}% {:>3} {:+.0f}%".format(
        raga, aA * 100, aB * 100, arrow, change * 100))

print()
if accB > accA + 0.01:
    print("  VERDICT: Hubness correction IMPROVES accuracy -> ADOPT")
elif accB >= accA - 0.01:
    print("  VERDICT: Hubness correction NEUTRAL -> adopt if wrongs decrease")
else:
    print("  VERDICT: Hubness correction HURTS accuracy -> DO NOT ADOPT")

print()
print("Done.")
