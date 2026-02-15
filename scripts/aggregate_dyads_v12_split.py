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
DYAD_BINS = 36
MIN_STABLE_FRAMES = 5
ALPHA = 0.5
EPS = 1e-8

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

VERSION_DIR = os.path.join(AGG_BASE_DIR, FEATURE_VERSION)
RUN_DIR = os.path.join(VERSION_DIR, f"run_{timestamp}")
DYAD_OUT_DIR = os.path.join(RUN_DIR, "dyad_stats")

os.makedirs(DYAD_OUT_DIR, exist_ok=True)


def compute_directional_dyads(f0, sa_hz, voiced_flag, bins=36, min_stable=5):
    valid_f0 = f0[voiced_flag]
    if len(valid_f0) < min_stable:
        return (
            np.zeros((bins, bins), dtype=np.float32),
            np.zeros((bins, bins), dtype=np.float32),
        )

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
            if count >= min_stable:
                stable_bins.append(current)
            current = b
            count = 1

    if count >= min_stable:
        stable_bins.append(current)

    mat_up = np.zeros((bins, bins), dtype=np.float32)
    mat_down = np.zeros((bins, bins), dtype=np.float32)

    for i in range(len(stable_bins) - 1):
        frm = stable_bins[i]
        to = stable_bins[i + 1]

        if to > frm:
            mat_up[frm, to] += 1
        elif to < frm:
            mat_down[frm, to] += 1

    # Laplace smoothing
    mat_up += ALPHA
    mat_down += ALPHA

    mat_up /= (np.sum(mat_up) + EPS)
    mat_down /= (np.sum(mat_down) + EPS)

    return mat_up, mat_down


def aggregate_dyads():
    raga_up = {}
    raga_down = {}
    clip_counts = {}

    for fname in os.listdir(FEATURES_DIR):
        if not fname.endswith(".npz"):
            continue

        data = np.load(os.path.join(FEATURES_DIR, fname), allow_pickle=True)

        raga = str(data["raga"])
        sa_hz = float(data["sa_hz"])
        f0 = data["f0"]
        voiced_flag = data["voiced_flag"]

        mat_up, mat_down = compute_directional_dyads(
            f0, sa_hz, voiced_flag, DYAD_BINS, MIN_STABLE_FRAMES
        )

        raga_up.setdefault(raga, []).append(mat_up)
        raga_down.setdefault(raga, []).append(mat_down)
        clip_counts[raga] = clip_counts.get(raga, 0) + 1

    for raga in raga_up.keys():
        up_array = np.array(raga_up[raga])
        down_array = np.array(raga_down[raga])

        mean_up = up_array.mean(axis=0)
        mean_down = down_array.mean(axis=0)

        std_up = up_array.std(axis=0)
        std_down = down_array.std(axis=0)

        np.savez(
            os.path.join(DYAD_OUT_DIR, f"{raga}_dyad_stats.npz"),
            mean_up=mean_up.flatten(),
            mean_down=mean_down.flatten(),
            std_up=std_up.flatten(),
            std_down=std_down.flatten(),
            bins=DYAD_BINS,
            min_stable_frames=MIN_STABLE_FRAMES,
            alpha=ALPHA,
            clip_count=clip_counts[raga],
            feature_version=FEATURE_VERSION,
        )

        print(f"[v1.2] Saved Dyads → {raga} (clips={clip_counts[raga]})")

    metadata = {
        "feature_version": FEATURE_VERSION,
        "bins": DYAD_BINS,
        "min_stable_frames": MIN_STABLE_FRAMES,
        "alpha": ALPHA,
        "timestamp": timestamp,
        "feature_source": FEATURES_DIR,
    }

    with open(os.path.join(RUN_DIR, "aggregation_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    print("\nDirectional Dyad Aggregation complete.")
    print("Saved to:", RUN_DIR)


if __name__ == "__main__":
    aggregate_dyads()
