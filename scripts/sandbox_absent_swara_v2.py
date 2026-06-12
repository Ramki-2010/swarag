"""
Sandbox v2: Absent-Swara Penalty using MUSICOLOGICAL swara definitions.

v1 FAILED because median-based "expected" detection was too noisy:
- Abhogi model had 18 "expected" bins (should be ~5 swaras)
- Self-harm: Abhogi clips missed their own expected bins
- Penalty hit everything equally -> net zero effect

v2 FIX: Use known swara positions for each raga. Each raga has a defined
set of swaras. Check if the test clip is MISSING swaras that the MODEL
raga requires. This is surgical: only penalizes when theory says it should.

KEY INSIGHT: Abhogi (S R2 G2 M2 D2) lacks Pa and Ni.
Kalyani (S R2 G2 M2 P D2 N3) requires Pa and Ni.
If test clip has no Pa/Ni -> penalize Kalyani score, not Abhogi score.
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

PER_RAGA_WEIGHTS = {
    "Bhairavi": (0.5, 0.5),
}

# =========================
# MUSICOLOGICAL SWARA DEFINITIONS
# =========================
# 72 bins, 16.67 cents/bin. Bin positions derived from ACTUAL PCD data
# (see _diag_bin_positions.py output), NOT from theoretical cent values.
#
# Carnatic pitch is relative to Sa (bin 0). After tonic normalization and
# modular folding to 0-1200 cents, swaras land at these empirical positions.
# Ranges are +-1 bin around peak to handle gamaka spread.
#
# KEY: These must match where energy ACTUALLY appears in the 72-bin PCD.

# Verified from _diag_bin_positions.py output on actual raga models:
#   Sa peak at bin 0 (0c)
#   Bhairavi b29=483c (Pa), Abhogi b42=700c, b59=983c
#   Kalyani b30=500c (Pa), b43=717c (N3-region)
#   Thodi   b41=683c, b29=483c
#   Mohanam b50=833c (D2), b30=500c (Pa), b19=317c
#   Saveri  b28=467c (Pa), b71=1183c, b27=450c
#   Shankar b47=783c, b48=800c, b17=283c

SWARA_BIN_RANGES = {
    "Sa":  (0, 2),     # bins 0-2   (0-33 cents)   — dominant in all ragas
    "R1":  (5, 8),     # bins 5-8   (83-133 cents)  — Bhairavi/Thodi/Saveri
    "R2":  (12, 14),   # bins 12-14 (200-233 cents)  — Abhogi b13
    "G2":  (10, 12),   # bins 10-12 (167-200 cents)  — Bhairavi b10,12
    "G3":  (17, 20),   # bins 17-20 (283-333 cents)  — Mohanam b19, Shankar b17
    "M1":  (17, 19),   # bins 17-19 (283-317 cents)  — Shankarabharanam b17-18
    "M2":  (27, 31),   # bins 27-31 (450-517 cents)  — Kalyani b28-31
    "Pa":  (27, 31),   # bins 27-31 (450-517 cents)  — overlaps M2! Same region.
    "D1":  (39, 43),   # bins 39-43 (650-717 cents)  — Bhairavi b39-42, Thodi b40-43
    "D2":  (49, 53),   # bins 49-53 (817-883 cents)  — Mohanam b50=833c
    "N2":  (58, 61),   # bins 58-61 (967-1017 cents)  — Abhogi b58-59
    "N3":  (69, 71),   # bins 69-71 (1150-1183 cents) — upper Sa octave boundary
}

# Ragas and their constituent swaras (arohana + avarohana combined)
RAGA_SWARAS = {
    "Kalyani":          ["Sa", "R2", "G3", "M2", "Pa", "D2", "N3"],
    "Abhogi":           ["Sa", "R2", "G2", "M2", "D2"],
    "Shankarabharanam": ["Sa", "R2", "G3", "M1", "Pa", "D2", "N3"],
    "Bhairavi":         ["Sa", "R1", "G2", "M1", "Pa", "D1", "N2"],
    "Thodi":            ["Sa", "R1", "G2", "M1", "Pa", "D1", "N2"],  # + N3 in avarohana
    "Mohanam":          ["Sa", "R2", "G3", "Pa", "D2"],
    "Saveri":           ["Sa", "R1", "M1", "Pa", "D1"],  # + G3, N3 sparingly
}


def swara_energy(pcd, swara_name):
    """Sum PCD energy in the bin range for a given swara."""
    if swara_name not in SWARA_BIN_RANGES:
        return 0.0
    lo, hi = SWARA_BIN_RANGES[swara_name]
    hi = min(hi, N_BINS - 1)
    return float(np.sum(pcd[lo:hi+1]))


def extract_features(data):
    """Extract PCD and directional dyads from feature file."""
    cents = data["cents_gated"]
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)

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
    all_pcds_arr = np.array(list(raga_mean_pcd.values()))
    threshold = 1.0 / N_BINS
    doc_freq = np.sum(all_pcds_arr > threshold, axis=0)
    idf = np.log(len(raga_mean_pcd) / (doc_freq + 1)) + 1
    bin_std = np.std(all_pcds_arr, axis=0)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * N_BINS
    return weights


# =========================
# PRE-FLIGHT: Verify swara energy in clips
# =========================
def run_preflight(clips, absent_energy_thresh=0.01):
    """
    Check swara energy for each clip against its OWN raga definition.
    If any clip is missing a swara its raga requires, the penalty could self-harm.
    """
    print("=" * 80)
    print("PRE-FLIGHT v2: Musicological swara energy check")
    print("absent_energy_thresh={} (sum of PCD in swara bin range)".format(
        absent_energy_thresh))
    print("=" * 80)

    # Part 1: Show swara energy for each raga (full model)
    print("\n[1] SWARA ENERGY PER RAGA MODEL (mean PCD)\n")
    raga_pcds = defaultdict(list)
    for c in clips:
        raga_pcds[c["raga"]].append(c["pcd"])
    raga_mean_pcd = {r: np.mean(v, axis=0) for r, v in raga_pcds.items()}

    for raga in sorted(RAGA_SWARAS.keys()):
        if raga not in raga_mean_pcd:
            continue
        swaras = RAGA_SWARAS[raga]
        energies = [(s, swara_energy(raga_mean_pcd[raga], s)) for s in swaras]
        energy_str = "  ".join("{}: {:.4f}".format(s, e) for s, e in energies)
        print("  {:20s} {}".format(raga, energy_str))

    # Also show energy for NON-raga swaras (what's absent in the model)
    print("\n[2] NON-RAGA SWARA ENERGY (swaras NOT in raga definition)\n")
    all_swaras = set(SWARA_BIN_RANGES.keys())
    for raga in sorted(RAGA_SWARAS.keys()):
        if raga not in raga_mean_pcd:
            continue
        absent_swaras = all_swaras - set(RAGA_SWARAS[raga])
        energies = [(s, swara_energy(raga_mean_pcd[raga], s)) for s in sorted(absent_swaras)]
        non_zero = [(s, e) for s, e in energies if e > 0.001]
        if non_zero:
            energy_str = "  ".join("{}: {:.4f}".format(s, e) for s, e in non_zero)
            print("  {:20s} {}".format(raga, energy_str))
        else:
            print("  {:20s} (all absent swaras near zero)".format(raga))

    # Part 3: Self-harm check - does any clip miss its own raga's swaras?
    print("\n[3] SELF-HARM CHECK (clip missing its OWN raga's swaras)\n")
    self_harm = False
    for c in clips:
        raga = c["raga"]
        if raga not in RAGA_SWARAS:
            continue
        missing = []
        for s in RAGA_SWARAS[raga]:
            e = swara_energy(c["pcd"], s)
            if e < absent_energy_thresh:
                missing.append((s, e))
        if missing:
            self_harm = True
            miss_str = ", ".join("{}({:.4f})".format(s, e) for s, e in missing)
            print("  WARN: {} ({}) missing: {}".format(
                c["fname"][:45], raga, miss_str))

    if not self_harm:
        print("  SAFE: All clips have their own raga's swaras present.")

    # Part 4: Cross-check - Abhogi clips vs Kalyani (should show Pa/Ni absent)
    print("\n[4] TARGET CHECK: Abhogi clips vs Kalyani swaras\n")
    kalyani_swaras = RAGA_SWARAS.get("Kalyani", [])
    abhogi_swaras = set(RAGA_SWARAS.get("Abhogi", []))
    extra_in_kalyani = [s for s in kalyani_swaras if s not in abhogi_swaras]
    print("  Kalyani has, Abhogi lacks: {}".format(extra_in_kalyani))
    print()
    for c in clips:
        if c["raga"] != "Abhogi":
            continue
        for s in extra_in_kalyani:
            e = swara_energy(c["pcd"], s)
            status = "ABSENT" if e < absent_energy_thresh else "PRESENT({:.4f})".format(e)
            print("    {} | {}: {}".format(c["fname"][:40], s, status))

    print()
    return self_harm


# =========================
# LOO with musicological absent-swara penalty
# =========================
def run_loo(clips, base_pcd_w=0.8, base_dyad_w=0.2,
            absent_penalty=0.0, absent_energy_thresh=0.01,
            label="", verbose=False):
    """
    LOO cross-validation with musicological absent-swara penalty.

    For each (test_clip, model_raga) pair:
    - Look up model_raga's required swaras from RAGA_SWARAS
    - Check if test clip has energy in each swara's bin range
    - Count how many required swaras are absent
    - Penalize: score *= (1 - penalty * absent_ratio)

    This only fires when the test clip is missing swaras the model raga
    REQUIRES. It does NOT fire on self-matches (clip has its own swaras).
    """
    correct = 0
    wrong = 0
    unknown = 0
    raga_stats = defaultdict(lambda: {"c": 0, "w": 0, "u": 0})
    wrong_to = defaultdict(int)
    penalty_log = []

    for i, held in enumerate(clips):
        train = [c for j, c in enumerate(clips) if j != i]

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

        idf_weights = compute_idf_weights(raga_mean_pcd)

        scores = {}
        for r in raga_mean_pcd:
            pcd_w, dyad_w = PER_RAGA_WEIGHTS.get(r, (base_pcd_w, base_dyad_w))

            pcd_weighted_test = held["pcd"] * idf_weights
            pcd_weighted_test /= (np.sum(pcd_weighted_test) + EPS)
            pcd_weighted_model = raga_mean_pcd[r] * idf_weights
            pcd_weighted_model /= (np.sum(pcd_weighted_model) + EPS)

            pcd_score = np.dot(pcd_weighted_test, pcd_weighted_model)
            dyad_score = (np.dot(held["up"], raga_mean_up[r]) +
                          np.dot(held["down"], raga_mean_down[r])) / 2

            raw_score = pcd_w * pcd_score + dyad_w * dyad_score

            # === MUSICOLOGICAL ABSENT-SWARA PENALTY ===
            if absent_penalty > 0 and r in RAGA_SWARAS:
                required_swaras = RAGA_SWARAS[r]
                n_required = len(required_swaras)
                absent_count = 0
                absent_names = []
                for s in required_swaras:
                    e = swara_energy(held["pcd"], s)
                    if e < absent_energy_thresh:
                        absent_count += 1
                        absent_names.append(s)

                if absent_count > 0 and n_required > 0:
                    absent_ratio = absent_count / n_required
                    penalty_factor = absent_penalty * absent_ratio
                    raw_score *= (1.0 - penalty_factor)

                    if verbose:
                        penalty_log.append({
                            "clip": held["fname"][:40],
                            "clip_raga": held["raga"],
                            "model_raga": r,
                            "absent": absent_names,
                            "n_absent": absent_count,
                            "n_required": n_required,
                            "penalty_pct": penalty_factor * 100
                        })

            scores[r] = raw_score

        ranking = sorted(scores.items(), key=lambda x: -x[1])
        margin = ranking[0][1] - ranking[1][1] if len(ranking) >= 2 else 0
        pred = ranking[0][0] if margin >= MARGIN_THRESH else "UNKNOWN"

        rs = raga_stats[held["raga"]]
        if pred == "UNKNOWN":
            unknown += 1; rs["u"] += 1
        elif pred == held["raga"]:
            correct += 1; rs["c"] += 1
        else:
            wrong += 1; rs["w"] += 1
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

    if verbose and penalty_log:
        print("\n  --- Penalty firings (unique clip_raga -> model_raga) ---")
        seen = set()
        for p in penalty_log:
            key = (p["clip_raga"], p["model_raga"])
            if key not in seen:
                seen.add(key)
                print("    {} -> {} model: missing {}/{} [{}] penalty={:.1f}%".format(
                    p["clip_raga"], p["model_raga"],
                    p["n_absent"], p["n_required"],
                    ",".join(p["absent"]), p["penalty_pct"]))

    print()
    return acc


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
    # STEP 0: PRE-FLIGHT — verify swara energy, check self-harm
    # ============================================================
    self_harm = run_preflight(clips, absent_energy_thresh=0.01)
    if self_harm:
        print("!!! SELF-HARM DETECTED — some clips missing their own swaras.")
        print("!!! Review above. May need to raise absent_energy_thresh.\n")

    # ============================================================
    # STEP 1: BASELINE
    # ============================================================
    print("=" * 80)
    print("BASELINE (no penalty)")
    print("=" * 80)
    run_loo(clips, 0.8, 0.2, absent_penalty=0.0,
            label="Baseline 0.8/0.2", verbose=False)

    # ============================================================
    # STEP 2: PENALTY SWEEP (absent_energy_thresh=0.01)
    # ============================================================
    print("=" * 80)
    print("PENALTY SWEEP (absent_energy_thresh=0.01)")
    print("=" * 80)
    for p in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
        run_loo(clips, 0.8, 0.2, absent_penalty=p,
                absent_energy_thresh=0.01,
                label="penalty={:.2f} thresh=0.010".format(p))

    # ============================================================
    # STEP 3: ENERGY THRESHOLD SWEEP (at penalty=0.15)
    # ============================================================
    print("=" * 80)
    print("ENERGY THRESHOLD SWEEP (penalty=0.15)")
    print("=" * 80)
    for t in [0.005, 0.008, 0.010, 0.015, 0.020, 0.030]:
        run_loo(clips, 0.8, 0.2, absent_penalty=0.15,
                absent_energy_thresh=t,
                label="penalty=0.15 thresh={:.3f}".format(t))

    # ============================================================
    # STEP 4: VERBOSE on best candidates
    # ============================================================
    print("=" * 80)
    print("VERBOSE DETAIL")
    print("=" * 80)
    run_loo(clips, 0.8, 0.2, absent_penalty=0.15,
            absent_energy_thresh=0.01,
            label="penalty=0.15 thresh=0.010 (verbose)", verbose=True)
    run_loo(clips, 0.8, 0.2, absent_penalty=0.20,
            absent_energy_thresh=0.01,
            label="penalty=0.20 thresh=0.010 (verbose)", verbose=True)

    print("=" * 80)
    print("DONE.")
    print("Target: Abhogi > 25%, overall >= 60.5%, Thodi/Saveri no regression.")
    print("=" * 80)
