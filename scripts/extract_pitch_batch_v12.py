import os
import librosa
import numpy as np
from datetime import datetime

# =========================
# CONFIG
# =========================
SR = 22050
FMIN = librosa.note_to_hz("C1")
FMAX = librosa.note_to_hz("C6")
PCD_BINS = 36

FEATURE_VERSION = "v1.2"

WINDOW_SIZE = 10
DRIFT_THRESHOLD = 25
VOICED_RATIO_THRESHOLD = 0.6
EPS = 1e-8

BASE_DIR = r"D:\Swaragam"
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "seed_carnatic")
FEATURE_DIR = os.path.join(BASE_DIR, "pcd_results", "features_v12")

os.makedirs(FEATURE_DIR, exist_ok=True)


# =========================
# TONIC SELECTION
# =========================
def choose_best_tonic(peaks_hz, pitch_values):
    candidates = []

    for hz in peaks_hz:
        for mult in (0.5, 1.0, 2.0):
            cand = hz * mult
            if 80 <= cand <= 400:
                candidates.append(cand)

    scores = []
    for cand in candidates:
        cents = 1200 * np.log2(pitch_values / cand)
        cents = cents[(cents > -1200) & (cents < 1200)]
        score = np.sum(np.abs(cents) < 50)
        scores.append(score)

    return candidates[np.argmax(scores)]


# =========================
# PITCH STABILITY GATE
# =========================
def apply_pitch_stability_gate(f0, sa_hz, voiced_flag):
    cents = np.zeros_like(f0)
    valid_idx = np.where(~np.isnan(f0))[0]

    cents[valid_idx] = 1200 * np.log2(f0[valid_idx] / sa_hz)
    cents = np.mod(cents, 1200)

    gated_mask = np.zeros_like(f0, dtype=bool)

    for i in range(0, len(f0) - WINDOW_SIZE):
        window = cents[i:i+WINDOW_SIZE]
        voiced_window = voiced_flag[i:i+WINDOW_SIZE]

        if np.mean(voiced_window) < VOICED_RATIO_THRESHOLD:
            continue

        c1 = np.mean(window[:WINDOW_SIZE//2])
        c2 = np.mean(window[WINDOW_SIZE//2:])
        drift = abs(c2 - c1)

        if drift < DRIFT_THRESHOLD:
            gated_mask[i:i+WINDOW_SIZE] = True

    gated_cents = cents[gated_mask]
    gating_ratio = np.sum(gated_mask) / (np.sum(voiced_flag) + EPS)

    return gated_cents, gating_ratio


# =========================
# PROCESS ONE FILE
# =========================
def process_file(audio_path, raga_label):

    y, sr = librosa.load(audio_path, sr=SR)

    f0, voiced_flag, _ = librosa.pyin(
        y, fmin=FMIN, fmax=FMAX, sr=sr
    )

    valid_f0 = f0[~np.isnan(f0)]
    if len(valid_f0) == 0:
        print(f"Skipped (no voiced): {audio_path}")
        return None

    hist, bin_edges = np.histogram(valid_f0, bins=200)
    top_idx = np.argsort(hist)[-5:]
    top_peaks = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in top_idx]

    sa_hz = choose_best_tonic(top_peaks, valid_f0)

    cents_gated, gating_ratio = apply_pitch_stability_gate(
        f0, sa_hz, voiced_flag
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(audio_path))[0]

    out_path = os.path.join(
        FEATURE_DIR,
        f"{base_name}_{timestamp}.npz"
    )

    np.savez(
        out_path,
        feature_version=FEATURE_VERSION,
        raga=raga_label,
        sa_hz=sa_hz,
        f0=f0,
        voiced_flag=voiced_flag,
        cents_gated=cents_gated,
        gating_ratio=gating_ratio,
        window_size=WINDOW_SIZE,
        drift_threshold=DRIFT_THRESHOLD,
        voiced_ratio_threshold=VOICED_RATIO_THRESHOLD,
    )

    print(f"{raga_label} | {base_name} | gating={gating_ratio:.3f}")

    return gating_ratio


# =========================
# BATCH PROCESS DATASET
# =========================
def batch_extract():

    total_files = 0
    gating_stats = {}

    for raga_folder in os.listdir(DATASET_DIR):
        raga_path = os.path.join(DATASET_DIR, raga_folder)

        if not os.path.isdir(raga_path):
            continue

        for file in os.listdir(raga_path):
            if not file.endswith(".wav"):
                continue

            audio_path = os.path.join(raga_path, file)
            ratio = process_file(audio_path, raga_folder)

            if ratio is not None:
                gating_stats.setdefault(raga_folder, []).append(ratio)
                total_files += 1

    print("\nExtraction Complete")
    print(f"Total files processed: {total_files}")

    for raga, ratios in gating_stats.items():
        print(f"{raga} | mean_gating={np.mean(ratios):.3f}")


if __name__ == "__main__":
    batch_extract()
