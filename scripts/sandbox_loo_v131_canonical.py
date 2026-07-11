"""
Canonical LOO cross-validation for v1.3.2.
Config: 7 ragas, 70 clips, 72-bin IDF x Variance,
        PCD=0.8/Dyad=0.2 global, NO per-raga overrides.
Bhairavi 0.5/0.5 override retired in v1.3.2 (LOO audit 2026-06-24 showed
it caused 9 Bhairavi wrongs and reduced overall accuracy by 3.6pp).
Excludes ragas below MIN_CLIPS_PER_RAGA=5 (Kamboji=3, Madhyamavati=2).
Run this to get ground-truth numbers for datasets.md and architecture.md.
"""
import os
import numpy as np

# ── Config (must match recognize_raga_v12.py exactly) ──────────────────────
N_BINS           = 72
MIN_STABLE_FRAMES = 5
ALPHA            = 0.01
EPS              = 1e-8
PCD_WEIGHT       = 0.8
DYAD_WEIGHT      = 0.2
PER_RAGA_WEIGHTS = {}  # Bhairavi override retired in v1.3.2
MARGIN_STRICT    = 0.003
MIN_MARGIN_FINAL = 0.001
MIN_CLIPS        = 5

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


# ── Feature loading ─────────────────────────────────────────────────────────
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


# ── IDF x Variance weights ──────────────────────────────────────────────────
def idf_var_weights(models):
    all_pcds  = np.array([m["pcd"] for m in models.values()])
    threshold = 1.0 / N_BINS
    doc_freq  = np.sum(all_pcds > threshold, axis=0)
    idf       = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std   = np.std(all_pcds, axis=0)
    w         = idf / (bin_std + EPS)
    return w / (np.sum(w) + EPS) * N_BINS


# ── LOO ─────────────────────────────────────────────────────────────────────
def run_loo(clips):
    # Pre-compute features
    processed = []
    for c in clips:
        pcd, up, down = compute_features(c["cents"])
        processed.append({"fname": c["fname"], "raga": c["raga"],
                          "pcd": pcd, "up": up, "down": down})

    raga_stats = {}
    total_c = total_w = total_u = 0
    wrongs  = []

    for i, held in enumerate(processed):
        train = processed[:i] + processed[i+1:]

        # Build per-raga models from training set
        raga_data = {}
        for c in train:
            raga_data.setdefault(c["raga"], []).append(c)

        models = {
            raga: {
                "pcd":  np.mean([c["pcd"]  for c in rclips], axis=0),
                "up":   np.mean([c["up"]   for c in rclips], axis=0),
                "down": np.mean([c["down"] for c in rclips], axis=0),
            }
            for raga, rclips in raga_data.items()
        }

        weights = idf_var_weights(models)

        # Score held-out clip
        pcd_w = held["pcd"] * weights
        pcd_w = pcd_w / (np.sum(pcd_w) + EPS)

        scores = {}
        for raga, m in models.items():
            r_pcd_w, r_dyad_w = PER_RAGA_WEIGHTS.get(raga, (PCD_WEIGHT, DYAD_WEIGHT))
            model_w = m["pcd"] * weights
            model_w = model_w / (np.sum(model_w) + EPS)
            pcd_sim  = np.dot(pcd_w, model_w)
            dyad_sim = 0.5 * (np.dot(held["up"],   m["up"]) +
                               np.dot(held["down"], m["down"]))
            scores[raga] = r_pcd_w * pcd_sim + r_dyad_w * dyad_sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0.0

        if margin >= MARGIN_STRICT:
            tier, pred = "HIGH", ranked[0][0]
        elif margin >= MIN_MARGIN_FINAL:
            tier, pred = "MOD",  ranked[0][0]
        else:
            tier, pred = "UNK",  "UNKNOWN"

        true_raga = held["raga"]
        s = raga_stats.setdefault(true_raga, {"t": 0, "c": 0, "w": 0, "u": 0})
        s["t"] += 1

        if pred == true_raga:
            s["c"] += 1; total_c += 1; sym = "+"
        elif tier == "UNK":
            s["u"] += 1; total_u += 1; sym = "?"
        else:
            s["w"] += 1; total_w += 1; sym = "X"
            wrongs.append((held["fname"][:50], true_raga, pred, round(margin, 5)))

        print("  {} {:<52} true={:<18} pred={:<18} m={:.5f}".format(
            sym, held["fname"][:52], true_raga, pred, margin))

    # ── Summary ──────────────────────────────────────────────────────────
    decided = total_c + total_w
    acc     = total_c / decided if decided > 0 else 0.0

    print()
    print("=" * 70)
    print("v1.3.1 CANONICAL LOO RESULTS (7 ragas, MIN_CLIPS={})".format(MIN_CLIPS))
    print("=" * 70)
    print("  Total : {}   Correct: {}   Wrong: {}   Unknown: {} ({:.0f}%)".format(
        len(processed), total_c, total_w, total_u,
        100 * total_u / len(processed)))
    print("  Accuracy (decided): {:.1f}%  ({}/{})".format(
        acc * 100, total_c, decided))
    print()
    print("  {:<22} {:>5} {:>7} {:>6} {:>8} {:>14}".format(
        "Raga", "Clips", "Correct", "Wrong", "Unknown", "Acc(decided)"))
    print("  " + "-" * 65)
    for raga in sorted(raga_stats.keys()):
        s  = raga_stats[raga]
        d  = s["t"] - s["u"]
        a  = s["c"] / d if d > 0 else 0.0
        ov = " <- override" if raga in PER_RAGA_WEIGHTS else ""
        print("  {:<22} {:>5} {:>7} {:>6} {:>8}    {:>6.0f}%{}".format(
            raga, s["t"], s["c"], s["w"], s["u"], a * 100, ov))

    if wrongs:
        print()
        print("  Wrongs:")
        for fname, tr, pr, m in wrongs:
            print("    {} ({}) -> {} (m={})".format(fname[:45], tr, pr, m))

    return total_c, total_w, total_u, acc, raga_stats


# ── Main ────────────────────────────────────────────────────────────────────
print("=" * 70)
print("Loading features from:", FEAT_DIR)
all_clips = load_clips()

# Apply MIN_CLIPS guardrail
from collections import Counter
raga_counts = Counter(c["raga"] for c in all_clips)
eligible    = {r for r, n in raga_counts.items() if n >= MIN_CLIPS}
clips       = [c for c in all_clips if c["raga"] in eligible]

print("All clips loaded: {}".format(len(all_clips)))
print("After MIN_CLIPS={} filter: {} clips, {} ragas".format(
    MIN_CLIPS, len(clips), len(eligible)))
print()
for raga in sorted(eligible):
    print("  {:<22} {}".format(raga, raga_counts[raga]))
print()

run_loo(clips)
