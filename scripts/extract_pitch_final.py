import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# =========================
# CONFIG
# =========================
SR = 22050
FMIN = librosa.note_to_hz("C1")
FMAX = librosa.note_to_hz("C6")
PCD_BINS = 36

# Soft human-voice tonic bounds (VERY permissive)
TONIC_MIN_HZ = 80
TONIC_MAX_HZ = 400

BASE_DIR = r"D:\Swagaram"
FEATURE_DIR = os.path.join(BASE_DIR, "pcd_results", "features")
FIGURE_DIR = os.path.join(BASE_DIR, "pcd_results", "Contours")

os.makedirs(FEATURE_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)


# =========================
# TONIC SELECTION
# =========================
def choose_best_tonic(peaks_hz, pitch_values):
    """
    Select best tonic candidate using octave expansion + plausibility.
    """
    candidates = []

    for hz in peaks_hz:
        for mult in [0.5, 1.0, 2.0]:
            cand = hz * mult
            if TONIC_MIN_HZ <= cand <= TONIC_MAX_HZ:
                candidates.append(cand)

    # Score candidates by how many pitches align near octave multiples
    scores = []
    for cand in candidates:
        cents = 1200 * np.log2(pitch_values / cand)
        cents = cents[(cents > -1200) & (cents < 1200)]
        score = np.sum(np.abs(cents) < 50)  # how often pitch ≈ Sa
        scores.append(score)

    best = candidates[np.argmax(scores)]
    return best


# =========================
# MAIN EXTRACTION
# =========================
def extract_pcd(audio_path, label, save_results=True):
    print("\n" + "=" * 30)
    print(f"Processing: {label}")
    print("=" * 30)

    y, sr = librosa.load(audio_path, sr=SR)

    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, fmin=FMIN, fmax=FMAX, sr=sr
    )

    times = librosa.times_like(f0, sr=sr)

    valid_f0 = f0[~np.isnan(f0)]
    print(f"Voiced frames: {len(valid_f0)} / {len(f0)}")

    # --- Histogram-based tonic candidates ---
    hist, bin_edges = np.histogram(valid_f0, bins=200)
    top_idx = np.argsort(hist)[-5:]
    top_peaks = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in top_idx]
    top_peaks = list(reversed(top_peaks))

    sa_hz = choose_best_tonic(top_peaks, valid_f0)

    print(f"Estimated Sa (Hz): {sa_hz:.2f}")
    print("Top 5 tonic candidates (Hz):", [round(p, 2) for p in top_peaks])

    # --- Pitch range ---
    print(f"Min pitch (Hz): {np.min(valid_f0):.2f}")
    print(f"Max pitch (Hz): {np.max(valid_f0):.2f}")

    # --- Cents normalization ---
    cents = 1200 * np.log2(valid_f0 / sa_hz)
    cents = cents[(cents > -1200) & (cents < 2400)]
    cents_mod = np.mod(cents, 1200)

    hist_pcd, _ = np.histogram(
        cents_mod, bins=PCD_BINS, range=(0, 1200), density=True
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # =========================
    # SAVE RESULTS
    # =========================
    if save_results:
        npz_path = os.path.join(
            FEATURE_DIR, f"{label}_{timestamp}.npz"
        )
        np.savez(
            npz_path,
            sa_hz=sa_hz,
            pcd=hist_pcd,
            pitch_range=(np.min(valid_f0), np.max(valid_f0))
        )
        print(f"Saved features → {npz_path}")

    # =========================
    # PLOTS
    # =========================
    # Pitch contour
    plt.figure(figsize=(12, 4))
    plt.plot(times, f0, linewidth=1)
    plt.axhline(sa_hz, color="orange", linestyle="--", label="Sa")
    plt.title(f"Pitch Contour — {label}")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.legend()

    contour_path = os.path.join(
        FIGURE_DIR, f"{label}_contour_{timestamp}.png"
    )
    plt.savefig(contour_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved contour → {contour_path}")

    # PCD plot
    plt.figure(figsize=(8, 4))
    plt.hist(
        cents_mod, bins=PCD_BINS, range=(0, 1200),
        density=True
    )
    plt.title(f"PCD ({PCD_BINS} bins) — {label}")
    plt.xlabel("Cents (Sa = 0)")
    plt.ylabel("Normalized Count")

    pcd_path = os.path.join(
        FIGURE_DIR, f"{label}_pcd_{timestamp}.png"
    )
    plt.savefig(pcd_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved PCD → {pcd_path}")


# =========================
# RUN (EDIT ONLY THIS)
# =========================
if __name__ == "__main__":
    audio_path = r"D:\Swagaram\datasets\seed_carnatic\Kalyani\Kalyani_clean_2.wav"
    label = "Kalyani_clean_2"

    extract_pcd(audio_path, label)