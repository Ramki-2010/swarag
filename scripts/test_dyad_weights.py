# =============================================================================
# TEST SCRIPT -- Dyad weight tuning
#
# Tests two weight configurations against baseline:
#   Baseline:    0.6 PCD / 0.4 Dyad  (current production)
#   Dyad-heavy:  0.3 PCD / 0.7 Dyad  (escalation weights as primary)
#   Dyad-only:   0.0 PCD / 1.0 Dyad  (extreme test)
#
# Goal: find the weight balance that gives Bhairavi AND Kalyani
# the best margins simultaneously.
# =============================================================================

import os
import numpy as np
import librosa
from utils import estimate_tonic

# =========================
# CONFIG
# =========================

N_BINS            = 36
MIN_STABLE_FRAMES = 5
ALPHA             = 0.5
EPS               = 1e-8

AGG_FOLDER = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260215_113720"

TEST_FILES = [
    ("Hamsadwani", "UNKNOWN",  r"D:\Swaragam\datasets\audio test\Alapana_HAM_Test.wav"),
    ("Mohanam",    "UNKNOWN",  r"D:\Swaragam\datasets\audio test\Alapana_Moha_Test.wav"),
    ("Bhairavi",   "Bhairavi", r"D:\Swaragam\datasets\audio test\Balap_Test.wav"),
    ("Kalyani",    "Kalyani",  r"D:\Swaragam\datasets\audio test\Kalap_Test.wav"),
]

WEIGHT_CONFIGS = [
    ("Baseline (0.6/0.4)", 0.6, 0.4),
    ("Dyad-heavy (0.3/0.7)", 0.3, 0.7),
    ("Dyad-only (0.0/1.0)", 0.0, 1.0),
]


# =========================
# MODEL LOADING
# =========================

def load_aggregated_models(aggregation_folder):
    models = {}
    pcd_folder  = os.path.join(aggregation_folder, "pcd_stats")
    dyad_folder = os.path.join(aggregation_folder, "dyad_stats")

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
                "mean_down": dyad_data["mean_down"],
            }
    return models


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
# SCORING (no genericness)
# =========================

def score_models(pcd, test_up, test_down, models, pcd_w, dyad_w):
    scores = {}
    for raga, model in models.items():
        pcd_sim  = np.dot(pcd, model["pcd"])
        up_sim   = np.dot(test_up, model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])
        dyad_sim = 0.5 * (up_sim + down_sim)
        scores[raga] = pcd_w * pcd_sim + dyad_w * dyad_sim
    return scores


# =========================
# EXTRACT FEATURES ONCE PER AUDIO
# =========================

def extract_features(audio_path):
    y, sr = librosa.load(audio_path, sr=22050)
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C1"),
                            fmax=librosa.note_to_hz("C6"), sr=22050)
    valid = f0[~np.isnan(f0)]

    if len(valid) < 200:
        return None, None, None

    sa_hz = estimate_tonic(valid)
    cents = 1200 * np.log2(valid / sa_hz) % 1200

    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    if np.sum(hist) == 0:
        return None, None, None

    pcd = hist / np.sum(hist)
    test_up, test_down = compute_directional_dyads(cents)
    return pcd, test_up, test_down


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print("\nSwarag -- Dyad Weight Tuning Test")
    print("=" * 70)

    models = load_aggregated_models(AGG_FOLDER)
    print(f"Models: {', '.join(sorted(models.keys()))}\n")

    # Extract features once per audio file
    features = {}
    for raga_name, expected, path in TEST_FILES:
        print(f"  Extracting: {os.path.basename(path)} ...", end=" ")
        pcd, up, down = extract_features(path)
        if pcd is not None:
            features[raga_name] = (pcd, up, down, expected)
            print("OK")
        else:
            print("FAILED (too few frames)")

    # Test each weight config
    for config_name, pcd_w, dyad_w in WEIGHT_CONFIGS:
        print(f"\n{'=' * 70}")
        print(f"  CONFIG: {config_name}")
        print(f"{'=' * 70}")

        for raga_name, (pcd, up, down, expected) in features.items():
            scores = score_models(pcd, up, down, models, pcd_w, dyad_w)
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0.0
            top1   = ranked[0][0]

            correct = (expected == "UNKNOWN" and top1 != expected) or (top1 == expected)
            # For "UNKNOWN" expected: we want it NOT to match confidently
            # Simple check: is top1 correct for trained ragas?
            if expected == "UNKNOWN":
                status = "OOD"
            elif top1 == expected:
                status = "CORRECT"
            else:
                status = "WRONG"

            print(f"\n  {raga_name:15} expect={expected:15} got={top1:20} margin={margin:.6f}  [{status}]")
            for r, s in ranked:
                print(f"    {r:20} {s:+.6f}")

    print(f"\n{'=' * 70}")
    print("Done.")
