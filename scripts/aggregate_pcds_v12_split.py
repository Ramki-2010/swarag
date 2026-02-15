# Deprecated: replaced by aggregate_all_v12.py

import os
import numpy as np
import json
from datetime import datetime

# =========================
# CONFIG
# =========================
FEATURES_DIR = r"D:\Swaragam\pcd_results\features_validated"
AGG_BASE_DIR = r"D:\Swaragam\pcd_results\aggregation"

FEATURE_VERSION = "v1.2"
N_BINS = 36
EPS = 1e-8

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

VERSION_DIR = os.path.join(AGG_BASE_DIR, FEATURE_VERSION)
RUN_DIR = os.path.join(VERSION_DIR, f"run_{timestamp}")
PCD_OUT_DIR = os.path.join(RUN_DIR, "pcd_stats")

os.makedirs(PCD_OUT_DIR, exist_ok=True)


def compute_pcd_from_pitch(f0, sa_hz, voiced_flag, bins=36):
    valid_f0 = f0[voiced_flag]
    if len(valid_f0) == 0:
        return np.zeros(bins, dtype=np.float32)

    cents = 1200 * np.log2(valid_f0 / sa_hz)
    cents = np.mod(cents, 1200)

    bin_edges = np.linspace(0, 1200, bins + 1)
    pitch_bins = np.digitize(cents, bin_edges) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < bins)]

    hist = np.zeros(bins, dtype=np.float32)
    for b in pitch_bins:
        hist[b] += 1

    hist /= (np.sum(hist) + EPS)
    return hist


def aggregate_pcds():
    raga_pcds = {}
    clip_counts = {}

    for fname in os.listdir(FEATURES_DIR):
        if not fname.endswith(".npz"):
            continue

        data = np.load(os.path.join(FEATURES_DIR, fname), allow_pickle=True)

        raga = str(data["raga"])
        sa_hz = float(data["sa_hz"])
        f0 = data["f0"]
        voiced_flag = data["voiced_flag"]

        pcd = compute_pcd_from_pitch(f0, sa_hz, voiced_flag, N_BINS)

        raga_pcds.setdefault(raga, []).append(pcd)
        clip_counts[raga] = clip_counts.get(raga, 0) + 1

    for raga, pcd_list in raga_pcds.items():
        pcd_array = np.array(pcd_list)
        mean_pcd = pcd_array.mean(axis=0)
        std_pcd = pcd_array.std(axis=0)

        np.savez(
            os.path.join(PCD_OUT_DIR, f"{raga}_pcd_stats.npz"),
            mean_pcd=mean_pcd,
            std_pcd=std_pcd,
            bins=N_BINS,
            clip_count=clip_counts[raga],
            feature_version=FEATURE_VERSION,
        )

        print(f"[v1.2] Saved PCD → {raga} (clips={clip_counts[raga]})")

    metadata = {
        "feature_version": FEATURE_VERSION,
        "bins": N_BINS,
        "eps": EPS,
        "timestamp": timestamp,
        "feature_source": FEATURES_DIR,
    }

    with open(os.path.join(RUN_DIR, "aggregation_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    print("\nPCD Aggregation complete.")
    print("Saved to:", RUN_DIR)


if __name__ == "__main__":
    aggregate_pcds()
