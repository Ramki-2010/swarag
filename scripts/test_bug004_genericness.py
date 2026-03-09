# =============================================================================
# TEST SCRIPT -- BUG-004 fix validation
# Genericness penalty: compute from MODEL PCD, not test PCD
#
# BEFORE (broken): genericness = entropy(test_pcd)
#   Same value for every raga -> no ranking effect -> useless
#
# AFTER (fix): genericness = entropy(model_pcd)
#   Generic models (Shankarabharanam) get penalized more
#   Specific models (Bhairavi) get penalized less
#
# Compare output against test_recognize_fix.py (the BEFORE baseline)
# =============================================================================

import os
import numpy as np
import librosa
from utils import estimate_tonic

# =========================
# CONFIG
# =========================

PCD_WEIGHT         = 0.6
DYAD_WEIGHT        = 0.4
GENERICNESS_WEIGHT = 0.05
N_BINS             = 36

# Using relaxed thresholds to see ranking effects clearly
MARGIN_STRICT     = 0.003
ESCALATION_MARGIN = 0.001
MIN_MARGIN_FINAL  = 0.0005

PCD_WEIGHT_ESC  = 0.3
DYAD_WEIGHT_ESC = 0.7

MIN_STABLE_FRAMES = 5
ALPHA             = 0.5
EPS               = 1e-8

AGG_FOLDER = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260215_113720"

TEST_FILES = {
    "Hamsadwani (not trained - expect UNKNOWN)" : r"D:\Swaragam\datasets\audio test\Alapana_HAM_Test.wav",
    "Mohanam    (not trained - expect UNKNOWN)" : r"D:\Swaragam\datasets\audio test\Alapana_Moha_Test.wav",
    "Bhairavi   (trained     - expect CORRECT)" : r"D:\Swaragam\datasets\audio test\Balap_Test.wav",
    "Kalyani    (trained     - expect CORRECT)" : r"D:\Swaragam\datasets\audio test\Kalap_Test.wav",
}


# =========================
# MODEL LOADING
# =========================

def load_aggregated_models(aggregation_folder):
    models = {}
    pcd_folder  = os.path.join(aggregation_folder, "pcd_stats")
    dyad_folder = os.path.join(aggregation_folder, "dyad_stats")

    if not os.path.exists(pcd_folder) or not os.path.exists(dyad_folder):
        return {}

    for fname in os.listdir(pcd_folder):
        if fname.endswith("_pcd_stats.npz"):
            raga      = fname.replace("_pcd_stats.npz", "")
            pcd_path  = os.path.join(pcd_folder, fname)
            dyad_path = os.path.join(dyad_folder, f"{raga}_dyad_stats.npz")

            if not os.path.exists(dyad_path):
                continue

            pcd_data  = np.load(pcd_path,  allow_pickle=True)
            dyad_data = np.load(dyad_path, allow_pickle=True)

            models[raga] = {
                "pcd":       pcd_data["mean_pcd"],
                "mean_up":   dyad_data["mean_up"],
                "mean_down": dyad_data["mean_down"]
            }

    return models


# =========================
# GENERICNESS PENALTY
# =========================

def compute_genericness(pcd):
    """Shannon entropy -- high entropy = generic/flat distribution."""
    return -np.sum(pcd * np.log(pcd + 1e-10))


# =========================
# DIRECTIONAL DYADS
# =========================

def compute_directional_dyads(cents):
    bins       = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    if len(pitch_bins) < MIN_STABLE_FRAMES:
        flat = np.zeros(N_BINS * N_BINS)
        return flat, flat

    stable_bins = []
    current     = pitch_bins[0]
    count       = 1

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
        frm = stable_bins[i]
        to  = stable_bins[i + 1]
        if to > frm:
            mat_up[frm, to]   += 1
        elif to < frm:
            mat_down[frm, to] += 1

    mat_up   += ALPHA
    mat_down += ALPHA
    mat_up   /= (np.sum(mat_up)   + EPS)
    mat_down /= (np.sum(mat_down) + EPS)

    return mat_up.flatten(), mat_down.flatten()


# =========================
# SCORING -- BUG-004 FIX
# =========================

def _score_models(pcd, test_up, test_down, models, pcd_w, dyad_w):
    scores = {}
    for raga, model in models.items():
        pcd_sim  = np.dot(pcd,       model["pcd"])
        up_sim   = np.dot(test_up,   model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])
        dyad_sim = 0.5 * (up_sim + down_sim)

        # BUG-004 FIX: genericness from MODEL PCD, not test PCD
        # Generic models (Shankarabharanam) penalized more
        # Specific models (Bhairavi) penalized less
        model_genericness = compute_genericness(model["pcd"])

        scores[raga] = (
            pcd_w  * pcd_sim +
            dyad_w * dyad_sim -
            GENERICNESS_WEIGHT * model_genericness
        )
    return scores


# =========================
# RECOGNITION
# =========================

def recognize_raga(audio_path, models):

    y, sr = librosa.load(audio_path, sr=22050)

    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C1"),
        fmax=librosa.note_to_hz("C6"),
        sr=22050,
    )

    valid = f0[~np.isnan(f0)]

    if len(valid) < 200:
        return {"final": "UNKNOWN / LOW CONFIDENCE", "ranking": [], "margin": 0.0, "confidence_tier": "UNKNOWN"}

    sa_hz = estimate_tonic(valid)
    cents = 1200 * np.log2(valid / sa_hz) % 1200

    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    if np.sum(hist) == 0:
        return {"final": "UNKNOWN / LOW CONFIDENCE", "ranking": [], "margin": 0.0, "confidence_tier": "UNKNOWN"}

    pcd = hist / np.sum(hist)

    test_up, test_down = compute_directional_dyads(cents)

    scores = _score_models(pcd, test_up, test_down, models, PCD_WEIGHT, DYAD_WEIGHT)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    margin = (ranked[0][1] - ranked[1][1]) if len(ranked) >= 2 else 0.0

    if margin >= MARGIN_STRICT:
        return {"final": ranked[0][0], "ranking": ranked, "margin": round(margin, 6), "confidence_tier": "HIGH"}

    esc_scores = _score_models(pcd, test_up, test_down, models, PCD_WEIGHT_ESC, DYAD_WEIGHT_ESC)
    esc_ranked = sorted(esc_scores.items(), key=lambda x: x[1], reverse=True)
    esc_margin = (esc_ranked[0][1] - esc_ranked[1][1]) if len(esc_ranked) >= 2 else 0.0

    if esc_margin >= MIN_MARGIN_FINAL:
        return {"final": esc_ranked[0][0], "ranking": esc_ranked, "margin": round(esc_margin, 6), "confidence_tier": "ESCALATED"}

    return {"final": "UNKNOWN / LOW CONFIDENCE", "ranking": esc_ranked, "margin": round(esc_margin, 6), "confidence_tier": "UNKNOWN"}


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print("\nSwarag -- BUG-004 Fix Test (genericness from MODEL PCD)")
    print("=" * 60)

    models = load_aggregated_models(AGG_FOLDER)
    print(f"Models loaded: {', '.join(sorted(models.keys()))}")

    # Show model genericness values so we can see the penalty difference
    print("\nModel genericness (entropy):")
    for raga in sorted(models.keys()):
        g = compute_genericness(models[raga]["pcd"])
        print(f"  {raga:20} : {g:.6f}")
    print()

    for label, path in TEST_FILES.items():
        print(f">> {label}")
        print(f"   File: {os.path.basename(path)}")

        result = recognize_raga(path, models)

        print(f"   Prediction      : {result['final']}")
        print(f"   Confidence Tier : {result['confidence_tier']}")
        print(f"   Margin          : {round(result['margin'], 6)}")
        print(f"   Ranking:")
        for raga, score in result["ranking"]:
            print(f"     {raga:20} | {round(score, 6)}")
        print()

    print("=" * 60)
    print("Test run complete.")
