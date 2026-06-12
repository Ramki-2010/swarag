"""
Sandbox: Absent-Swara Penalty for janya/parent raga separation.

PROBLEM: Abhogi (S R2 G2 M2 D2) is a strict subset of Kalyani (S R2 G2 M2 P D2 N3).
PCD dot-product always favors Kalyani because it has all of Abhogi's swaras plus more.
Weight overrides at every level gave 0% for Abhogi (L-044).

INSIGHT: The discriminative signal is what's MISSING. If a test clip lacks Pa and Ni,
it should NOT score well against Kalyani (which expects Pa and Ni).

MECHANISM: For each raga model, identify expected strong swaras (bins where model PCD
is well above background). For each test clip, check if those swaras are absent.
If so, penalize that raga's score.

Tests: penalty strengths 0.10, 0.15, 0.20 with LOO cross-validation on 7 ragas.
"""
import os
import numpy as np
from collections import defaultdict

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
N_BINS = 72
ALPHA = 0.01
EPS = 1e-8
MIN_STABLE = 5
MARGIN_THRESH = 0.001

MODELED = {"Bhairavi", "Kalyani", "Mohanam", "Shankarabharanam", "Thodi", "Abhogi", "Saveri"}

# Per-raga weight overrides (same as production v1.3.1)
PER_RAGA_WEIGHTS = {
    "Bhairavi": (0.5, 0.5),
}


def extract_features(data):
    """Extract PCD and directional dyads from feature file."""
    cents = data["cents_gated"]
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)

    # Stable-region dyads (mirrors aggregation)
    bins_arr = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins_arr) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    stable_bins = []
    if len(pitch_bins) >= MIN_STABLE:
        current = pitch_bins[0]
        count = 1
        for b in pitch_bins[1:]:
            if b == current:
                count += 1
            else:
                if count >= MIN_STABLE:
                    stable_bins.append(current)
                current = b
                count = 1
        if count >= MIN_STABLE:
            stable_bins.append(current)

    up = np.zeros((N_BINS, N_BINS))
    down = np.zeros((N_BINS, N_BINS))

    for i in range(len(stable_bins) - 1):
        frm = stable_bins[i]
        to = stable_bins[i + 1]
        if to > frm:
            up[frm, to] += 1
        elif to < frm:
            down[frm, to] += 1

    up_flat = (up + ALPHA).flatten()
    up_flat /= (np.sum(up_flat) + EPS)
    down_flat = (down + ALPHA).flatten()
    down_flat /= (np.sum(down_flat) + EPS)

    return pcd, up_flat, down_flat


def load_clips():
    """Load all modeled clips from feature directory."""
    clips = []
    for f in sorted(os.listdir(FEAT_DIR)):
        if not f.endswith(".npz"):
            continue
        fpath = os.path.join(FEAT_DIR, f)
        if os.path.isdir(fpath):
            continue
        d = np.load(fpath, allow_pickle=True)
        if str(d.get("feature_version", "")) != "v1.2":
            continue
        if float(d["gating_ratio"]) < 0.05:
            continue
        raga = str(d["raga"])
        if raga not in MODELED:
            continue
        cents = d["cents_gated"]
        if len(cents) < 200:
            continue
        pcd, up, down = extract_features(d)
        clips.append({"fname": f, "raga": raga, "pcd": pcd, "up": up, "down": down})
    return clips


def compute_idf_weights(raga_mean_pcd):
    """Compute IDF x variance weights from raga mean PCDs."""
    all_pcds_arr = np.array(list(raga_mean_pcd.values()))
    threshold = 1.0 / N_BINS
    doc_freq = np.sum(all_pcds_arr > threshold, axis=0)
    idf = np.log(len(raga_mean_pcd) / (doc_freq + 1)) + 1
    bin_std = np.std(all_pcds_arr, axis=0)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * N_BINS
    return weights


def run_loo(clips, base_pcd_w=0.8, base_dyad_w=0.2,
            absent_penalty=0.0, expected_thresh=2.0, absent_thresh=0.005,
            label="", verbose=False):
    """
    LOO cross-validation with optional absent-swara penalty.

    absent_penalty: max score reduction (0.0 = disabled, 0.15 = 15% max penalty)
    expected_thresh: multiplier of median to define "expected" swara bins
    absent_thresh: PCD value below which a bin is considered "absent" in test clip
    """
    correct = 0
    wrong = 0
    unknown = 0
    raga_stats = defaultdict(lambda: {"c": 0, "w": 0, "u": 0})
    wrong_to = defaultdict(int)
    penalty_applied = []  # Track when penalty actually fires

    for i, held in enumerate(clips):
        train = [c for j, c in enumerate(clips) if j != i]

        # Build LOO models
        raga_pcds = defaultdict(list)
        raga_ups = defaultdict(list)
        raga_downs = defaultdict(list)
        for c in train:
            raga_pcds[c["raga"]].append(c["pcd"])
            raga_ups[c["raga"]].append(c["up"])
            raga_downs[c["raga"]].append(c["down"])

        raga_mean_pcd = {r: np.mean(v, axis=0) for r, v in raga_pcds.items()}
        raga_mean_up = {r: np.mean(v, axis=0) for r, v in raga_ups.items()}
        raga_mean_down = {r: np.mean(v, axis=0) for r, v in raga_downs.items()}

        # IDF x variance weights
        idf_weights = compute_idf_weights(raga_mean_pcd)

        # Score each raga
        scores = {}
        for r in raga_mean_pcd:
            pcd_w, dyad_w = PER_RAGA_WEIGHTS.get(r, (base_pcd_w, base_dyad_w))

            # Weighted PCD similarity
            pcd_weighted_test = held["pcd"] * idf_weights
            pcd_weighted_test /= (np.sum(pcd_weighted_test) + EPS)
            pcd_weighted_model = raga_mean_pcd[r] * idf_weights
            pcd_weighted_model /= (np.sum(pcd_weighted_model) + EPS)

            pcd_score = np.dot(pcd_weighted_test, pcd_weighted_model)
            dyad_score = (np.dot(held["up"], raga_mean_up[r]) +
                          np.dot(held["down"], raga_mean_down[r])) / 2

            raw_score = pcd_w * pcd_score + dyad_w * dyad_score

            # === ABSENT-SWARA PENALTY ===
            if absent_penalty > 0:
                model_pcd = raga_mean_pcd[r]
                # Only consider bins that actually have signal
                active_bins = model_pcd[model_pcd > 0]
                if len(active_bins) > 0:
                    median_strength = np.median(active_bins)
                    # "Expected swaras" = bins where model has > threshold * median
                    expected_mask = model_pcd > (expected_thresh * median_strength)
                    n_expected = np.sum(expected_mask)
                    if n_expected > 0:
                        # How many expected bins are absent in test clip?
                        absent_count = np.sum(expected_mask & (held["pcd"] < absent_thresh))
                        absent_ratio = absent_count / n_expected
                        penalty = absent_penalty * absent_ratio
                        raw_score *= (1.0 - penalty)

                        if verbose and absent_count > 0:
                            penalty_applied.append({
                                "clip": held["fname"][:40],
                                "clip_raga": held["raga"],
                                "model_raga": r,
                                "expected": int(n_expected),
                                "absent": int(absent_count),
                                "ratio": absent_ratio,
                                "penalty_pct": penalty * 100
                            })

            scores[r] = raw_score

        ranking = sorted(scores.items(), key=lambda x: -x[1])
        margin = ranking[0][1] - ranking[1][1] if len(ranking) >= 2 else 0

        pred = ranking[0][0] if margin >= MARGIN_THRESH else "UNKNOWN"

        rs = raga_stats[held["raga"]]
        if pred == "UNKNOWN":
            unknown += 1
            rs["u"] += 1
        elif pred == held["raga"]:
            correct += 1
            rs["c"] += 1
        else:
            wrong += 1
            rs["w"] += 1
            wrong_to[ranking[0][0]] += 1

    decided = correct + wrong
    acc = correct / decided if decided > 0 else 0

    print("{:55s} C={:2d} W={:2d} U={:2d} Acc={:.1f}%".format(
        label, correct, wrong, unknown, acc * 100))
    for r in sorted(raga_stats.keys()):
        s = raga_stats[r]
        d = s["c"] + s["w"]
        a = s["c"] / d * 100 if d > 0 else 0
        print("  {:20s} {:2d}c {:2d}w {:2d}u ({:.0f}%)".format(
            r, s["c"], s["w"], s["u"], a))
    if wrong_to:
        sinks = ", ".join("{}={}".format(r, c)
                          for r, c in sorted(wrong_to.items(), key=lambda x: -x[1])[:5])
        print("  Sink: {}".format(sinks))

    if verbose and penalty_applied:
        print("\n  --- Penalty details (top 10) ---")
        # Show unique clip-model pairs where penalty fired
        seen = set()
        shown = 0
        for p in penalty_applied:
            key = (p["clip_raga"], p["model_raga"])
            if key not in seen:
                seen.add(key)
                print("    {} clip vs {} model: {}/{} expected absent, penalty={:.1f}%".format(
                    p["clip_raga"], p["model_raga"],
                    p["absent"], p["expected"], p["penalty_pct"]))
                shown += 1
                if shown >= 10:
                    break

    print()
    return acc


# =========================
# DIAGNOSTIC: Expected-swara map & self-harm check
# =========================

# Approximate swara names for 72-bin PCD (17 cents/bin)
SWARA_LABELS = {
    0: "Sa",   # 0 cents
    6: "R1",   # ~100 cents
    8: "R2",   # ~133 cents
    12: "G2",  # ~200 cents
    14: "G3",  # ~233 cents
    18: "M1",  # ~300 cents
    21: "M2",  # ~350 cents
    30: "Pa",  # ~500 cents
    35: "D1",  # ~583 cents
    37: "D2",  # ~617 cents
    42: "N2",  # ~700 cents
    44: "N3",  # ~733 cents
}

def bin_to_swara(b):
    """Map a 72-bin index to nearest swara name."""
    cents = b * (1200.0 / N_BINS)
    best = None
    best_dist = 999
    for sb, name in SWARA_LABELS.items():
        sc = sb * (1200.0 / N_BINS)
        if abs(cents - sc) < best_dist:
            best_dist = abs(cents - sc)
            best = name
    return "{}(b{}={:.0f}c)".format(best, b, cents)


def run_preflight(clips, expected_thresh=2.0, absent_thresh=0.005):
    """
    SAFETY CHECK: Before running any penalty, show:
    1. Which bins each raga model considers 'expected'
    2. For every clip vs its OWN raga: does the penalty fire? (MUST be zero)
    3. For Abhogi clips vs Kalyani: does the penalty fire? (SHOULD be >0)
    """
    print("=" * 80)
    print("PRE-FLIGHT DIAGNOSTIC (expected_thresh={}, absent_thresh={})".format(
        expected_thresh, absent_thresh))
    print("=" * 80)

    # Build full models (no LOO, just for diagnostic)
    raga_pcds = defaultdict(list)
    for c in clips:
        raga_pcds[c["raga"]].append(c["pcd"])
    raga_mean_pcd = {r: np.mean(v, axis=0) for r, v in raga_pcds.items()}

    # --- Part 1: Expected swara map for each raga ---
    print("\n[1] EXPECTED SWARA MAP (bins > {:.1f}x median)\n".format(expected_thresh))
    raga_expected = {}
    for raga in sorted(raga_mean_pcd.keys()):
        model_pcd = raga_mean_pcd[raga]
        active = model_pcd[model_pcd > 0]
        if len(active) == 0:
            continue
        median_str = np.median(active)
        expected_mask = model_pcd > (expected_thresh * median_str)
        expected_bins = np.where(expected_mask)[0]
        raga_expected[raga] = expected_bins
        swara_names = [bin_to_swara(b) for b in expected_bins]
        print("  {:20s} {:2d} expected bins: {}".format(
            raga, len(expected_bins), ", ".join(swara_names)))
    print()

    # --- Part 2: Self-harm check ---
    print("[2] SELF-HARM CHECK (clip vs its OWN raga model)")
    print("    If any self-match shows absent swaras, the penalty will HURT.\n")
    self_harm_found = False
    for c in clips:
        raga = c["raga"]
        if raga not in raga_expected:
            continue
        expected_bins = raga_expected[raga]
        if len(expected_bins) == 0:
            continue
        absent_in_clip = [b for b in expected_bins if c["pcd"][b] < absent_thresh]
        if len(absent_in_clip) > 0:
            self_harm_found = True
            names = [bin_to_swara(b) for b in absent_in_clip]
            print("  WARNING: {} ({}) missing {}/{} expected: {}".format(
                c["fname"][:45], raga,
                len(absent_in_clip), len(expected_bins),
                ", ".join(names)))

    if not self_harm_found:
        print("  SAFE: No clip is missing expected swaras of its own raga.")
    print()

    # --- Part 3: Cross-match check (Abhogi vs Kalyani, and others) ---
    print("[3] CROSS-MATCH CHECK (clip vs OTHER raga models)")
    print("    Shows where the penalty WOULD fire across ragas.\n")

    # Build a summary: for each (clip_raga, model_raga) pair, count penalty firings
    cross_penalties = defaultdict(lambda: {"total_clips": 0, "penalty_clips": 0,
                                           "avg_absent": [], "swaras": set()})
    for c in clips:
        for model_raga in sorted(raga_expected.keys()):
            if model_raga == c["raga"]:
                continue  # skip self
            expected_bins = raga_expected[model_raga]
            if len(expected_bins) == 0:
                continue
            absent_in_clip = [b for b in expected_bins if c["pcd"][b] < absent_thresh]
            key = (c["raga"], model_raga)
            cross_penalties[key]["total_clips"] += 1
            if len(absent_in_clip) > 0:
                cross_penalties[key]["penalty_clips"] += 1
                cross_penalties[key]["avg_absent"].append(
                    len(absent_in_clip) / len(expected_bins))
                for b in absent_in_clip:
                    cross_penalties[key]["swaras"].add(bin_to_swara(b))

    # Print only pairs where penalty fires on at least 1 clip
    print("  {:20s} {:20s} {:>5s} {:>6s} {:>8s}  Missing swaras".format(
        "Clip Raga", "Model Raga", "Fires", "Total", "Avg%"))
    print("  " + "-" * 78)
    for (cr, mr) in sorted(cross_penalties.keys()):
        info = cross_penalties[(cr, mr)]
        if info["penalty_clips"] == 0:
            continue
        avg_pct = np.mean(info["avg_absent"]) * 100
        swaras = ", ".join(sorted(info["swaras"]))
        print("  {:20s} {:20s} {:5d} {:6d} {:7.1f}%  {}".format(
            cr, mr, info["penalty_clips"], info["total_clips"],
            avg_pct, swaras))
    print()

    return self_harm_found


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    clips = load_clips()

    raga_counts = defaultdict(int)
    for c in clips:
        raga_counts[c["raga"]] += 1
    print("Loaded {} clips:".format(len(clips)))
    for r in sorted(raga_counts.keys()):
        print("  {:20s} {:2d} clips".format(r, raga_counts[r]))
    print()

    # ============================================================
    # STEP 0: PRE-FLIGHT — safety check before any penalty runs
    # ============================================================
    self_harm = run_preflight(clips, expected_thresh=2.0, absent_thresh=0.005)
    if self_harm:
        print("!!! SELF-HARM DETECTED — review warnings above before proceeding.")
        print("!!! Penalty may hurt clips that are missing their own raga's swaras.")
        print()

    # ============================================================
    # STEP 1: BASELINE (no penalty) — must match v1.3.1 LOO results
    # ============================================================
    print("=" * 80)
    print("BASELINE (no absent-swara penalty)")
    print("=" * 80)
    run_loo(clips, 0.8, 0.2, absent_penalty=0.0,
            label="Baseline 0.8/0.2 (no penalty)", verbose=True)

    # ============================================================
    # STEP 2: ABSENT-SWARA PENALTY SWEEP
    # ============================================================
    print("=" * 80)
    print("ABSENT-SWARA PENALTY SWEEP (expected_thresh=2.0, absent_thresh=0.005)")
    print("=" * 80)
    for penalty in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        run_loo(clips, 0.8, 0.2, absent_penalty=penalty,
                label="Penalty={:.2f}".format(penalty))

    # ============================================================
    # STEP 3: BEST PENALTY WITH VERBOSE (show where penalty fires)
    # ============================================================
    print("=" * 80)
    print("VERBOSE: Best candidates with penalty detail")
    print("=" * 80)
    run_loo(clips, 0.8, 0.2, absent_penalty=0.15,
            label="Penalty=0.15 (verbose)", verbose=True)
    run_loo(clips, 0.8, 0.2, absent_penalty=0.20,
            label="Penalty=0.20 (verbose)", verbose=True)

    # ============================================================
    # STEP 4: EXPECTED THRESHOLD SWEEP (how strict is "expected"?)
    # ============================================================
    print("=" * 80)
    print("EXPECTED THRESHOLD SWEEP (penalty=0.15)")
    print("=" * 80)
    for thresh in [1.5, 2.0, 2.5, 3.0]:
        run_loo(clips, 0.8, 0.2, absent_penalty=0.15,
                expected_thresh=thresh,
                label="Penalty=0.15, expected_thresh={:.1f}".format(thresh))

    # ============================================================
    # STEP 5: ABSENT THRESHOLD SWEEP (how low is "absent"?)
    # ============================================================
    print("=" * 80)
    print("ABSENT THRESHOLD SWEEP (penalty=0.15, expected_thresh=2.0)")
    print("=" * 80)
    for at in [0.002, 0.005, 0.010, 0.015]:
        run_loo(clips, 0.8, 0.2, absent_penalty=0.15,
                absent_thresh=at,
                label="Penalty=0.15, absent_thresh={:.3f}".format(at))

    print("=" * 80)
    print("DONE. Compare Abhogi accuracy and overall accuracy across configs.")
    print("Target: Abhogi > 25%, overall > 67.4%, no regressions on Thodi/Saveri.")
    print("=" * 80)
