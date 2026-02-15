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

SCHEMA_VERSION = "1.1"

BASE_DIR = r"D:\Swagaram"
FEATURE_DIR = os.path.join(BASE_DIR, "pcd_results", "features_raw")
FIGURE_DIR = os.path.join(BASE_DIR, "pcd_results", "Contours")

os.makedirs(FEATURE_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)


# =========================
# TONIC CANDIDATE SELECTION
# =========================
def choose_best_tonic(peaks_hz, pitch_values):
    """
    Generate a best-guess tonic.
    Final sanity validation is intentionally deferred.
    """
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

    best = candidates[np.argmax(scores)]
    return best, candidates


# =========================
# MAIN EXTRACTION
# =========================
def extract_pcd(audio_path, label):
    print("\n" + "=" * 40)
    print(f"Processing: {label}")
    print("=" * 40)

    y, sr = librosa.load(audio_path, sr=SR)

    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, fmin=FMIN, fmax=FMAX, sr=sr
    )

    times = librosa.times_like(f0, sr=sr)

    valid_f0 = f0[~np.isnan(f0)]
    print(f"Voiced frames: {len(valid_f0)} / {len(f0)}")

    if len(valid_f0) == 0:
        raise RuntimeError("No voiced frames detected.")

    # --- Histogram-based tonic candidates ---
    hist, bin_edges = np.histogram(valid_f0, bins=200)
    top_idx = np.argsort(hist)[-5:]
    top_peaks = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in top_idx]
    top_peaks = list(reversed(top_peaks))

    sa_hz, tonic_candidates = choose_best_tonic(top_peaks, valid_f0)

    print(f"Estimated Sa (Hz): {sa_hz:.2f}")
    print("Tonic candidates (Hz):", [round(x, 2) for x in tonic_candidates])

    # --- Cents normalization ---
    cents = 1200 * np.log2(valid_f0 / sa_hz)
    cents = cents[(cents > -1200) & (cents < 2400)]
    cents_mod = np.mod(cents, 1200)

    pcd, _ = np.histogram(
        cents_mod, bins=PCD_BINS, range=(0, 1200)
    )
    pcd = pcd / np.sum(pcd)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # =========================
    # SAVE FEATURES (RAW)
    # =========================
    npz_path = os.path.join(
        FEATURE_DIR, f"{label}_{timestamp}.npz"
    )

    np.savez(
        npz_path,
        schema_version=SCHEMA_VERSION,
        raga=label.split("_")[0],
        sa_hz=sa_hz,
        tonic_candidates=np.array(tonic_candidates),
        pcd=pcd,
        f0=f0,
        voiced_flag=voiced_flag,
        min_pitch=np.nanmin(valid_f0),
        max_pitch=np.nanmax(valid_f0)
    )

    print(f"Saved raw features → {npz_path}")

    # =========================
    # PLOTS
    # =========================
    plt.figure(figsize=(12, 4))
    plt.plot(times, f0, linewidth=0.8)
    plt.axhline(sa_hz, color="orange", linestyle="--", label="Sa")
    plt.title(f"Pitch Contour — {label}")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.legend()
    plt.tight_layout()

    contour_path = os.path.join(
        FIGURE_DIR, f"{label}_contour_{timestamp}.png"
    )
    plt.savefig(contour_path, dpi=150)
    plt.close()

    plt.figure(figsize=(8, 4))
    bins = np.linspace(0, 1200, PCD_BINS + 1)
    plt.stairs(pcd, bins, fill=True)
    plt.title(f"PCD — {label}")
    plt.xlabel("Cents (Sa = 0)")
    plt.ylabel("Normalized Count")
    plt.tight_layout()

    pcd_path = os.path.join(
        FIGURE_DIR, f"{label}_pcd_{timestamp}.png"
    )
    plt.savefig(pcd_path, dpi=150)
    plt.close()

    print(f"Saved contour → {contour_path}")
    print(f"Saved PCD → {pcd_path}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    audio_path = r"D:\Swagaram\datasets\seed_carnatic\Shankarabharanam\Shankarabharanam_1.wav"
    label = "Shankarabharanam_1"
    
    extract_pcd(audio_path, label)