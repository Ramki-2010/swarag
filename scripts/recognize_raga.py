import os
import sys
import numpy as np
import librosa
from scipy.spatial.distance import jensenshannon

from utils import estimate_tonic

# =========================
# CONFIG
# =========================
SR = 22050
MAX_DURATION_SEC = 360  # 6-minute cap — kept intentionally

AGG_BASE_DIR = r"D:\Swaragam\pcd_results\aggregation"
STATS_DIR = os.path.join(AGG_BASE_DIR, "stats")

N_BINS = 36

# Sibling pairs for conditional dyad escalation
SIBLINGS = {
    "Kalyani": "Shankarabharanam",
    "Shankarabharanam": "Kalyani",
    # Add more pairs later as needed
}

# =========================
# FEATURE EXTRACTION (GLOBAL)
# =========================
def extract_features_from_audio(y):
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C1"),
        fmax=librosa.note_to_hz("C6"),
        sr=SR
    )

    valid_f0 = f0[voiced_flag]
    if len(valid_f0) < 200:
        raise ValueError("Not enough voiced frames")

    sa_hz = estimate_tonic(valid_f0)

    cents = 1200 * np.log2(valid_f0 / sa_hz)
    cents = np.mod(cents, 1200)

    # ---- PCD ----
    pcd, _ = np.histogram(
        cents,
        bins=N_BINS,
        range=(0, 1200),
        density=True
    )

    # ---- DYADS (transition matrix) ----
    bin_idx = np.floor(cents / (1200 / N_BINS)).astype(int)
    bin_idx = np.clip(bin_idx, 0, N_BINS - 1)

    dyad_mat = np.zeros((N_BINS, N_BINS))
    for i in range(len(bin_idx) - 1):
        dyad_mat[bin_idx[i], bin_idx[i + 1]] += 1

    if dyad_mat.sum() > 0:
        dyad_mat /= dyad_mat.sum()

    dyad = dyad_mat.flatten()

    return pcd, dyad


# =========================
# LOAD SIGNATURES
# =========================
def load_signatures():
    signatures = {}

    for fname in os.listdir(STATS_DIR):
        if not fname.endswith("_pcd_stats.npz"):
            continue

        raga = fname.replace("_pcd_stats.npz", "")

        pcd_path = os.path.join(STATS_DIR, fname)
        dyad_path = os.path.join(STATS_DIR, f"{raga}_dyad_stats.npz")

        try:
            pcd_data = np.load(pcd_path)
            dyad_data = np.load(dyad_path)
        except FileNotFoundError:
            print(f"Missing dyad file for {raga}")
            continue

        signatures[raga] = {
            "pcd": pcd_data["mean_pcd"],
            "dyad": dyad_data["mean_dyads"].flatten()
        }

    if not signatures:
        raise RuntimeError("No raga signatures found")

    return signatures


# =========================
# DISTANCE (used for both normal and escalated)
# =========================
def distance(pcd_a, dyad_a, pcd_b, dyad_b, pcd_weight=0.6, dyad_weight=0.4):
    d_pcd = jensenshannon(pcd_a, pcd_b)
    d_dyad = jensenshannon(dyad_a, dyad_b)
    return pcd_weight * d_pcd + dyad_weight * d_dyad


# =========================
# GLOBAL RECOGNITION with CONDITIONAL DYAD ESCALATION (v1.1 final)
# =========================
def recognize_raga(audio_path):
    print(f"\nAnalyzing: {os.path.basename(audio_path)}")

    y, sr = librosa.load(
        audio_path,
        sr=SR,
        duration=MAX_DURATION_SEC
    )

    signatures = load_signatures()

    pcd, dyad = extract_features_from_audio(y)

    # Normal scoring (0.6 PCD / 0.4 dyad)
    normal_dist = {}
    for raga, sig in signatures.items():
        d = distance(pcd, dyad, sig["pcd"], sig["dyad"], pcd_weight=0.6, dyad_weight=0.4)
        normal_dist[raga] = d

    scores = sorted(normal_dist.items(), key=lambda x: x[1])
    best_raga = scores[0][0]
    second_raga = scores[1][0] if len(scores) > 1 else None
    margin_12 = scores[1][1] - scores[0][1] if len(scores) > 1 else float('inf')

    # === CONDITIONAL DYAD ESCALATION ===
    if (margin_12 < 0.08 and
        second_raga == SIBLINGS.get(best_raga, None)):
        print("Sibling tie detected — escalating dyad weight (0.2 PCD / 0.8 dyad)")
        escalated_dist = {}
        for raga, sig in signatures.items():
            d = distance(pcd, dyad, sig["pcd"], sig["dyad"], pcd_weight=0.2, dyad_weight=0.8)
            escalated_dist[raga] = d

        scores = sorted(escalated_dist.items(), key=lambda x: x[1])

    # === TIERED CONDITIONAL CONFIDENCE ===
    best_raga, best_score = scores[0]
    second_score = scores[1][1] if len(scores) > 1 else float('inf')
    third_score  = scores[2][1] if len(scores) > 2 else float('inf')

    margin_12 = second_score - best_score
    margin_23 = third_score - second_score if len(scores) > 2 else float('inf')

    if margin_12 < 0.03:
        prediction = "UNKNOWN / LOW CONFIDENCE"
    elif margin_12 < 0.06 and margin_23 < 0.03:
        prediction = "UNKNOWN / LOW CONFIDENCE"
    else:
        prediction = best_raga

    print(f"Final Prediction: {prediction}")
    print("Ranking:")
    for r, s in scores:
        print(f"{r:20s} | {s:.3f}")

    return prediction, scores


# =========================
# CLI
# =========================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recognize_raga.py <path_to_audio.wav>")
        sys.exit(1)

    audio = sys.argv[1]
    recognize_raga(audio)