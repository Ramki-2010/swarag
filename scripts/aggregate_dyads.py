import os
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
FEATURES_DIR = r"D:\Swaragam\pcd_results\features_validated"
OUT_DIR = r"D:\Swaragam\pcd_results\aggregation\stats"

DYAD_BINS = 36
MIN_STABLE_FRAMES = 5
EPS = 1e-8

os.makedirs(OUT_DIR, exist_ok=True)


def compute_dyads_from_pitch(f0, sa_hz, voiced_flag, bins=36, min_stable_frames=5):
    valid_f0 = f0[voiced_flag]
    if len(valid_f0) < min_stable_frames:
        return np.zeros(bins * bins, dtype=np.float32)

    cents = 1200 * np.log2(valid_f0 / sa_hz)
    cents = np.mod(cents, 1200)

    bin_edges = np.linspace(0, 1200, bins + 1)
    pitch_bins = np.digitize(cents, bin_edges) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < bins)]

    stable_bins = []
    current = pitch_bins[0]
    count = 1

    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= min_stable_frames:
                stable_bins.append(current)
            current = b
            count = 1

    if count >= min_stable_frames:
        stable_bins.append(current)

    mat = np.zeros((bins, bins), dtype=np.float32)
    for i in range(len(stable_bins) - 1):
        mat[stable_bins[i], stable_bins[i + 1]] += 1

    mat /= (np.sum(mat) + EPS)
    return mat.flatten()


def aggregate_dyads():
    raga_dyads = {}

    for fname in os.listdir(FEATURES_DIR):
        if not fname.endswith(".npz"):
            continue

        data = np.load(os.path.join(FEATURES_DIR, fname), allow_pickle=True)

        raga = str(data["raga"])
        sa_hz = float(data["sa_hz"])
        f0 = data["f0"]
        voiced_flag = data["voiced_flag"]

        dyad = compute_dyads_from_pitch(
            f0, sa_hz, voiced_flag, DYAD_BINS, MIN_STABLE_FRAMES
        )

        raga_dyads.setdefault(raga, []).append(dyad)

    for raga, dyads in raga_dyads.items():
        dyads = np.array(dyads)
        mean_dyad = dyads.mean(axis=0)
        std_dyad = dyads.std(axis=0)

        np.savez(
            os.path.join(OUT_DIR, f"{raga}_dyad_stats.npz"),
            mean_dyads=mean_dyad,
            std_dyads=std_dyad,
            bins=DYAD_BINS,
            min_stable_frames=MIN_STABLE_FRAMES,
        )

        mat = mean_dyad.reshape(DYAD_BINS, DYAD_BINS)
        plt.figure(figsize=(8, 6))
        plt.imshow(mat, origin="lower", cmap="magma")
        plt.title(f"{raga} – Stable Dyads (min={MIN_STABLE_FRAMES})")
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(os.path.join(OUT_DIR, f"{raga}_stable_dyad_visual.png"))
        plt.close()

        print(f"Saved dyads → {raga}")


if __name__ == "__main__":
    aggregate_dyads()
