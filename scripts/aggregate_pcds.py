import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# =========================
# CONFIG
# =========================
FEATURES_DIR = r"D:\Swaragam\pcd_results\features_validated"
AGG_BASE_DIR = r"D:\Swaragam\pcd_results\aggregation"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = os.path.join(AGG_BASE_DIR, f"run_{timestamp}")

DYAD_OUT_DIR = os.path.join(RUN_DIR, "dyad_stats")
VISUAL_DIR = os.path.join(RUN_DIR, "visuals")

os.makedirs(DYAD_OUT_DIR, exist_ok=True)
os.makedirs(VISUAL_DIR, exist_ok=True)

N_BINS = 36
MIN_STABLE = 5


# =========================
# DYAD COMPUTATION
# =========================
def compute_stable_dyads(cents):
    bins = np.floor(cents / (1200 / N_BINS)).astype(int)
    dyad = np.zeros((N_BINS, N_BINS))

    stable = 1
    for i in range(1, len(bins)):
        if bins[i] == bins[i - 1]:
            stable += 1
        else:
            if stable >= MIN_STABLE:
                dyad[bins[i - 1], bins[i]] += 1
            stable = 1

    return dyad


# =========================
# AGGREGATION
# =========================
def aggregate_dyads():
    raga_dyads = {}

    for fname in os.listdir(FEATURES_DIR):
        if not fname.endswith(".npz"):
            continue

        data = np.load(os.path.join(FEATURES_DIR, fname), allow_pickle=True)
        raga = str(data["raga"])
        cents = data["cents"]

        dyad = compute_stable_dyads(cents)

        raga_dyads.setdefault(raga, []).append(dyad)

    for raga, mats in raga_dyads.items():
        mats = np.array(mats)
        mean_dyad = np.mean(mats, axis=0)
        mean_flat = mean_dyad.flatten()
        mean_flat /= mean_flat.sum()

        out_path = os.path.join(DYAD_OUT_DIR, f"{raga}_dyad_stats.npz")
        np.savez(out_path, mean=mean_flat)

        # ---- Visual Diagnostic ----
        plt.figure(figsize=(7, 6))
        plt.imshow(mean_dyad, origin="lower", cmap="magma")
        plt.title(f"{raga} – Stable Dyads (min={MIN_STABLE})")
        plt.xlabel("To Bin")
        plt.ylabel("From Bin")
        plt.colorbar()
        plt.tight_layout()

        vis_path = os.path.join(VISUAL_DIR, f"{raga}_stable_dyads.png")
        plt.savefig(vis_path)
        plt.close()

        print(f"Saved dyads → {raga}")

    print("\nAggregation run saved to:")
    print(RUN_DIR)


if __name__ == "__main__":
    aggregate_dyads()
