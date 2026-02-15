import os
import numpy as np
import json
from datetime import datetime

# =========================
# CONFIG
# =========================
BASE_DIR = r"D:\Swaragam"
FEATURES_DIR = os.path.join(BASE_DIR, "pcd_results", "features_v12")
AGG_BASE_DIR = os.path.join(BASE_DIR, "pcd_results", "aggregation")

FEATURE_VERSION = "v1.2"

N_BINS = 36
MIN_STABLE_FRAMES = 5
ALPHA = 0.5
EPS = 1e-8

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

VERSION_DIR = os.path.join(AGG_BASE_DIR, FEATURE_VERSION)
RUN_DIR = os.path.join(VERSION_DIR, f"run_{timestamp}")

PCD_DIR = os.path.join(RUN_DIR, "pcd_stats")
DYAD_DIR = os.path.join(RUN_DIR, "dyad_stats")

os.makedirs(PCD_DIR, exist_ok=True)
os.makedirs(DYAD_DIR, exist_ok=True)


# =========================
# PCD FROM GATED CENTS
# =========================
def compute_pcd_from_gated(cents_gated):
    if len(cents_gated) == 0:
        return np.zeros(N_BINS)

    hist, _ = np.histogram(
        cents_gated,
        bins=N_BINS,
        range=(0, 1200)
    )

    hist = hist / (np.sum(hist) + EPS)
    return hist


# =========================
# DIRECTIONAL DYADS FROM GATED CENTS
# =========================
def compute_directional_dyads_from_gated(cents_gated):

    if len(cents_gated) < MIN_STABLE_FRAMES:
        return (
            np.zeros((N_BINS, N_BINS)),
            np.zeros((N_BINS, N_BINS)),
            0
        )

    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents_gated, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    stable_bins = []
    current = pitch_bins[0]
    count = 1

    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current = b
            count = 1

    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)

    mat_up = np.zeros((N_BINS, N_BINS))
    mat_down = np.zeros((N_BINS, N_BINS))

    transitions = 0

    for i in range(len(stable_bins) - 1):
        frm = stable_bins[i]
        to = stable_bins[i + 1]

        if to > frm:
            mat_up[frm, to] += 1
            transitions += 1
        elif to < frm:
            mat_down[frm, to] += 1
            transitions += 1

    # Laplace smoothing
    mat_up += ALPHA
    mat_down += ALPHA

    mat_up /= (np.sum(mat_up) + EPS)
    mat_down /= (np.sum(mat_down) + EPS)

    return mat_up, mat_down, transitions


# =========================
# MAIN AGGREGATION
# =========================
def aggregate_all():

    raga_pcds = {}
    raga_up = {}
    raga_down = {}
    raga_gating = {}
    raga_transitions = {}
    clip_counts = {}

    total_files_seen = 0
    skipped_files = 0

    if not os.path.exists(FEATURES_DIR):
        raise RuntimeError(f"Features directory not found: {FEATURES_DIR}")

    for fname in os.listdir(FEATURES_DIR):

        if not fname.endswith(".npz"):
            continue

        total_files_seen += 1

        data = np.load(os.path.join(FEATURES_DIR, fname), allow_pickle=True)

        # Guardrail: correct feature version only
        if "feature_version" not in data or str(data["feature_version"]) != FEATURE_VERSION:
            skipped_files += 1
            continue

        raga = str(data["raga"])
        cents_gated = data["cents_gated"]
        gating_ratio = float(data["gating_ratio"])

        # Guardrail: skip extremely low gating
        if gating_ratio < 0.05:
            skipped_files += 1
            continue

        pcd = compute_pcd_from_gated(cents_gated)
        up, down, transitions = compute_directional_dyads_from_gated(cents_gated)

        raga_pcds.setdefault(raga, []).append(pcd)
        raga_up.setdefault(raga, []).append(up)
        raga_down.setdefault(raga, []).append(down)
        raga_gating.setdefault(raga, []).append(gating_ratio)
        raga_transitions.setdefault(raga, []).append(transitions)

        clip_counts[raga] = clip_counts.get(raga, 0) + 1

    # =========================
    # SAVE PER RAGA
    # =========================
    for raga in raga_pcds.keys():

        mean_pcd = np.mean(raga_pcds[raga], axis=0)
        std_pcd = np.std(raga_pcds[raga], axis=0)

        mean_up = np.mean(raga_up[raga], axis=0)
        mean_down = np.mean(raga_down[raga], axis=0)

        std_up = np.std(raga_up[raga], axis=0)
        std_down = np.std(raga_down[raga], axis=0)

        mean_gating = float(np.mean(raga_gating[raga]))
        mean_transitions = float(np.mean(raga_transitions[raga]))

        np.savez(
            os.path.join(PCD_DIR, f"{raga}_pcd_stats.npz"),
            mean_pcd=mean_pcd,
            std_pcd=std_pcd,
            bins=N_BINS,
            clip_count=clip_counts[raga],
            mean_gating_ratio=mean_gating,
            feature_version=FEATURE_VERSION,
        )

        np.savez(
            os.path.join(DYAD_DIR, f"{raga}_dyad_stats.npz"),
            mean_up=mean_up.flatten(),
            mean_down=mean_down.flatten(),
            std_up=std_up.flatten(),
            std_down=std_down.flatten(),
            bins=N_BINS,
            alpha=ALPHA,
            mean_transitions=mean_transitions,
            clip_count=clip_counts[raga],
            feature_version=FEATURE_VERSION,
        )

        print(f"[v1.2] {raga} | clips={clip_counts[raga]} | "
              f"mean_gating={mean_gating:.3f} | "
              f"mean_transitions={mean_transitions:.1f}")

    # =========================
    # GLOBAL METADATA
    # =========================
    metadata = {
        "feature_version": FEATURE_VERSION,
        "bins": N_BINS,
        "min_stable_frames": MIN_STABLE_FRAMES,
        "alpha": ALPHA,
        "timestamp": timestamp,
        "feature_source": FEATURES_DIR,
        "total_files_seen": total_files_seen,
        "skipped_files": skipped_files
    }

    with open(os.path.join(RUN_DIR, "aggregation_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    print("\n✔ v1.2 Aggregation complete")
    print("Saved to:", RUN_DIR)
    print(f"Files seen: {total_files_seen} | Skipped: {skipped_files}")


if __name__ == "__main__":
    aggregate_all()
