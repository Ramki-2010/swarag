"""
Confusion matrix audit for v1.3.1 LOO.
Built on top of sandbox_loo_v131_canonical.py infrastructure.
Fixes vs old confusion_matrix_audit.py:
  - No fragile imports from sandbox_absent_swara_v2
  - PER_RAGA_WEIGHTS applied correctly (Bhairavi 0.5/0.5)
  - IDF x Variance weights recomputed per LOO fold (not cached globally)
  - Raga-exclusion audit runs a clean sub-LOO, not a filtered global model
Runs two scenarios:
  1. Full 7-raga LOO (canonical baseline)
  2. 7-raga LOO WITHOUT Bhairavi override (tests if override helps or hurts)
  3. 5-raga LOO excluding Bhairavi + Abhogi (upper-bound for stable ragas)
"""
import os
import numpy as np
from collections import Counter

# ── Config (must match recognize_raga_v12.py exactly) ──────────────────────
N_BINS            = 72
MIN_STABLE_FRAMES = 5
ALPHA             = 0.01
EPS               = 1e-8
PCD_WEIGHT        = 0.8
DYAD_WEIGHT       = 0.2
PER_RAGA_WEIGHTS  = {"Bhairavi": (0.5, 0.5)}
MARGIN_STRICT     = 0.003
MIN_MARGIN_FINAL  = 0.001
MIN_CLIPS         = 5

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


# ── Feature loading (shared with canonical LOO script) ──────────────────────
def load_clips():
    clips = []
    for fname in sorted(os.listdir(FEAT_DIR)):
        if not fname.endswith(".npz"):
            continue
        path = os.path.join(FEAT_DIR, fname)
        d = np.load(path, allow_pickle=True)
        if "feature_version" not in d or str(d["feature_version"]) != "v1.2":
            continue
        if float(d["gating_ratio"]) < 0.05:
            continue
        cents = d["cents_gated"]
        if len(cents) < 200:
            continue
        clips.append({"fname": fname, "raga": str(d["raga"]), "cents": cents})
    return clips


# ── Feature computation ─────────────────────────────────────────────────────
def compute_features(cents):
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)

    bin_edges  = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bin_edges) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    stable_bins = []
    current = pitch_bins[0]
    count   = 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current = b
            count   = 1
    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)

    mat_up   = np.zeros((N_BINS, N_BINS))
    mat_down = np.zeros((N_BINS, N_BINS))
    for i in range(len(stable_bins) - 1):
        frm, to = stable_bins[i], stable_bins[i + 1]
        if to > frm:
            mat_up[frm, to]   += 1
        elif to < frm:
            mat_down[frm, to] += 1

    mat_up   += ALPHA;  mat_up   /= (np.sum(mat_up)   + EPS)
    mat_down += ALPHA;  mat_down /= (np.sum(mat_down) + EPS)

    return pcd, mat_up.flatten(), mat_down.flatten()


# ── IDF x Variance weights (recomputed per fold) ────────────────────────────
def idf_var_weights(models):
    all_pcds  = np.array([m["pcd"] for m in models.values()])
    threshold = 1.0 / N_BINS
    doc_freq  = np.sum(all_pcds > threshold, axis=0)
    idf       = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std   = np.std(all_pcds, axis=0)
    w         = idf / (bin_std + EPS)
    return w / (np.sum(w) + EPS) * N_BINS


# ── Core LOO with confusion matrix ─────────────────────────────────────────
def run_loo_cm(processed, label, per_raga_weights=None):
    """Full LOO with per-fold weight recomputation and confusion matrix output.
    per_raga_weights: dict of {raga: (pcd_w, dyad_w)} overrides, or None for global only.
    """
    if per_raga_weights is None:
        per_raga_weights = {}

    ragas       = sorted(set(c["raga"] for c in processed))
    conf        = {tr: {pr: 0 for pr in ragas + ["UNKNOWN"]} for tr in ragas}
    raga_stats  = {r: {"t": 0, "c": 0, "w": 0, "u": 0} for r in ragas}
    total_c = total_w = total_u = 0

    for i, held in enumerate(processed):
        train = processed[:i] + processed[i+1:]

        raga_data = {}
        for c in train:
            raga_data.setdefault(c["raga"], []).append(c)

        # Recompute models and weights fresh for this fold
        models = {
            raga: {
                "pcd":  np.mean([c["pcd"]  for c in rclips], axis=0),
                "up":   np.mean([c["up"]   for c in rclips], axis=0),
                "down": np.mean([c["down"] for c in rclips], axis=0),
            }
            for raga, rclips in raga_data.items()
        }
        weights = idf_var_weights(models)

        pcd_w = held["pcd"] * weights
        pcd_w = pcd_w / (np.sum(pcd_w) + EPS)

        scores = {}
        for raga, m in models.items():
            r_pcd_w, r_dyad_w = per_raga_weights.get(raga, (PCD_WEIGHT, DYAD_WEIGHT))
            model_w = m["pcd"] * weights
            model_w = model_w / (np.sum(model_w) + EPS)
            pcd_sim  = np.dot(pcd_w, model_w)
            dyad_sim = 0.5 * (np.dot(held["up"],   m["up"]) +
                               np.dot(held["down"], m["down"]))
            scores[raga] = r_pcd_w * pcd_sim + r_dyad_w * dyad_sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0.0

        if   margin >= MARGIN_STRICT:    tier, pred = "HIGH", ranked[0][0]
        elif margin >= MIN_MARGIN_FINAL: tier, pred = "MOD",  ranked[0][0]
        else:                            tier, pred = "UNK",  "UNKNOWN"

        true_raga = held["raga"]
        s = raga_stats[true_raga]
        s["t"] += 1
        conf[true_raga][pred] += 1

        if pred == true_raga:
            s["c"] += 1; total_c += 1
        elif tier == "UNK":
            s["u"] += 1; total_u += 1
        else:
            s["w"] += 1; total_w += 1

    # ── Print results ────────────────────────────────────────────────────
    decided = total_c + total_w
    acc     = total_c / decided if decided > 0 else 0.0

    print()
    print("=" * 70)
    print(label)
    print("=" * 70)
    print("  Total: {}  Correct: {}  Wrong: {}  Unknown: {}  Acc: {:.1f}%".format(
        len(processed), total_c, total_w, total_u, acc * 100))

    # Per-raga summary
    print()
    print("  {:<22} {:>5} {:>7} {:>6} {:>8} {:>13}".format(
        "Raga", "Clips", "Correct", "Wrong", "Unknown", "Acc(decided)"))
    print("  " + "-" * 62)
    for raga in ragas:
        s = raga_stats[raga]
        d = s["t"] - s["u"]
        a = s["c"] / d if d > 0 else 0.0
        print("  {:<22} {:>5} {:>7} {:>6} {:>8}    {:>6.0f}%".format(
            raga, s["t"], s["c"], s["w"], s["u"], a * 100))

    # Confusion matrix
    print()
    print("  Confusion matrix (rows=true, cols=predicted):")
    col_w = 6
    header = "  {:<22}".format("") + "".join(
        ["{:>{}}" .format(r[:col_w], col_w + 1) for r in ragas]) + "{:>{}}" .format("UNK", col_w + 1)
    print(header)
    print("  " + "-" * (22 + (len(ragas) + 1) * (col_w + 1)))
    for tr in ragas:
        row = "  {:<22}".format(tr)
        for pr in ragas:
            val = conf[tr][pr]
            marker = "*" if (val > 0 and pr != tr) else " "
            row += "{:>{}}" .format(str(val) + marker, col_w + 1)
        row += "{:>{}}" .format(str(conf[tr]["UNKNOWN"]), col_w + 1)
        print(row)

    return total_c, total_w, total_u, acc


# ── Main ────────────────────────────────────────────────────────────────────
print("=" * 70)
print("Loading features...")
all_clips = load_clips()

raga_counts = Counter(c["raga"] for c in all_clips)
eligible    = {r for r, n in raga_counts.items() if n >= MIN_CLIPS}
clips       = [c for c in all_clips if c["raga"] in eligible]

print("Eligible clips: {} ({} ragas)".format(len(clips), len(eligible)))

# Pre-compute features once
processed = []
for c in clips:
    pcd, up, down = compute_features(c["cents"])
    processed.append({"fname": c["fname"], "raga": c["raga"],
                      "pcd": pcd, "up": up, "down": down})

# ── Scenario 1: Full 7-raga, WITH Bhairavi override (canonical) ────────────
c1, w1, u1, a1 = run_loo_cm(
    processed,
    "SCENARIO 1: 7 ragas, WITH Bhairavi 0.5/0.5 override (CANONICAL)",
    per_raga_weights=PER_RAGA_WEIGHTS
)

# ── Scenario 2: Full 7-raga, WITHOUT Bhairavi override ─────────────────────
c2, w2, u2, a2 = run_loo_cm(
    processed,
    "SCENARIO 2: 7 ragas, NO Bhairavi override (global 0.8/0.2 only)",
    per_raga_weights={}
)

# ── Scenario 3: 5-raga, Bhairavi + Abhogi excluded ─────────────────────────
exclude      = {"Bhairavi", "Abhogi"}
proc_5raga   = [c for c in processed if c["raga"] not in exclude]
c3, w3, u3, a3 = run_loo_cm(
    proc_5raga,
    "SCENARIO 3: 5 ragas, Bhairavi + Abhogi excluded (upper-bound stable ragas)",
    per_raga_weights={}
)

# ── Comparison summary ──────────────────────────────────────────────────────
print()
print("=" * 70)
print("SUMMARY COMPARISON")
print("=" * 70)
print("  {:<52} {:>7} {:>6} {:>6} {:>8}".format(
    "Scenario", "Correct", "Wrong", "Unk", "Acc"))
print("  " + "-" * 82)
for label, c, w, u, a in [
    ("1. 7-raga + Bhairavi override (canonical)", c1, w1, u1, a1),
    ("2. 7-raga, no override",                   c2, w2, u2, a2),
    ("3. 5-raga, Bhairavi+Abhogi excluded",       c3, w3, u3, a3),
]:
    print("  {:<52} {:>7} {:>6} {:>6}  {:>6.1f}%".format(label, c, w, u, a * 100))
print()