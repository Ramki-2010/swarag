import os
import numpy as np
import json

# =========================
# CONFIG
# =========================
AGG_RUN_FOLDER = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260215_113720"

GENERICNESS_LAMBDA = 0.15
MIN_TRANSITIONS = 50
EPS = 1e-8

PCD_DIR = os.path.join(AGG_RUN_FOLDER, "pcd_stats")
DYAD_DIR = os.path.join(AGG_RUN_FOLDER, "dyad_stats")

# Load metadata
with open(os.path.join(AGG_RUN_FOLDER, "aggregation_metadata.json")) as f:
    META = json.load(f)

N_BINS = META["bins"]

# Use same gating parameters as extraction
WINDOW_SIZE = META.get("window_size", 10)
DRIFT_THRESHOLD = META.get("drift_threshold", 25)
VOICED_RATIO_THRESHOLD = META.get("voiced_ratio_threshold", 0.6)


# =========================
# UTILITIES
# =========================
def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + EPS)


def entropy(p):
    p = p[p > 0]
    return -np.sum(p * np.log(p + EPS))


def asymmetry(up, down):
    up = up / (np.sum(up) + EPS)
    down = down / (np.sum(down) + EPS)
    return np.sum(up * np.log((up + EPS) / (down + EPS)))


def compute_genericness(pcd, up, down):
    H = entropy(pcd) / np.log(len(pcd))
    A = 1 / (1 + asymmetry(up.flatten(), down.flatten()))
    omission = 1 - (np.sum(pcd < 0.01) / len(pcd))
    return np.clip(H * A * omission, 0, 1)


# =========================
# PITCH STABILITY GATE (Inference)
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
# LOAD MODELS
# =========================
def load_models():
    models = {}

    for fname in os.listdir(PCD_DIR):
        if not fname.endswith("_pcd_stats.npz"):
            continue

        raga = fname.replace("_pcd_stats.npz", "")

        pcd_data = np.load(os.path.join(PCD_DIR, fname))
        dyad_data = np.load(os.path.join(DYAD_DIR, f"{raga}_dyad_stats.npz"))

        models[raga] = {
            "pcd": pcd_data["mean_pcd"],
            "up": dyad_data["mean_up"],
            "down": dyad_data["mean_down"],
        }

    return models


MODELS = load_models()


# =========================
# FEATURE COMPUTATION
# =========================
def compute_features(f0, sa_hz, voiced_flag):

    gated_cents, gating_ratio = apply_pitch_stability_gate(
        f0, sa_hz, voiced_flag
    )

    if len(gated_cents) == 0:
        return None

    # --- PCD ---
    hist, _ = np.histogram(
        gated_cents,
        bins=N_BINS,
        range=(0, 1200)
    )
    hist = hist / (np.sum(hist) + EPS)

    # --- Directional Dyads ---
    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(gated_cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    up = np.zeros((N_BINS, N_BINS))
    down = np.zeros((N_BINS, N_BINS))
    transitions = 0

    current = pitch_bins[0]
    count = 1
    stable_bins = []

    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= META["min_stable_frames"]:
                stable_bins.append(current)
            current = b
            count = 1

    if count >= META["min_stable_frames"]:
        stable_bins.append(current)

    for i in range(len(stable_bins) - 1):
        frm = stable_bins[i]
        to = stable_bins[i + 1]

        if to > frm:
            up[frm, to] += 1
            transitions += 1
        elif to < frm:
            down[frm, to] += 1
            transitions += 1

    up = up / (np.sum(up) + EPS)
    down = down / (np.sum(down) + EPS)

    return hist, up, down, transitions, gating_ratio


# =========================
# RECOGNITION
# =========================
def recognize_raga(f0, sa_hz, voiced_flag):

    features = compute_features(f0, sa_hz, voiced_flag)
    if features is None:
        return None

    hist, up, down, transitions, gating_ratio = features

    g_index = compute_genericness(hist, up, down)

    results = {}

    for raga, model in MODELS.items():

        pcd_sim = cosine(hist, model["pcd"])
        dyad_sim = 0.5 * cosine(up.flatten(), model["up"]) + \
                   0.5 * cosine(down.flatten(), model["down"])

        raw_score = 0.5 * pcd_sim + 0.5 * dyad_sim

        if transitions < MIN_TRANSITIONS:
            final_score = raw_score * 0.9
        else:
            final_score = raw_score * (1 - GENERICNESS_LAMBDA * g_index)

        results[raga] = {
            "raw": raw_score,
            "final": final_score,
            "genericness": g_index,
            "transitions": transitions,
            "gating_ratio": gating_ratio
        }

    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1]["final"],
        reverse=True
    )

    return sorted_results
