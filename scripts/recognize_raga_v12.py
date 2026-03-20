import os
import traceback
import numpy as np
import librosa

from utils import estimate_tonic   # C1: single canonical tonic source

# =========================
# CONFIG
# =========================

SR               = 22050
MAX_DURATION_SEC = 360   # 6-minute cap per file
PCD_WEIGHT       = 0.6
DYAD_WEIGHT      = 0.4
GENERICNESS_WEIGHT = 0.0   # BUG-004 fix: confirmed inert, removed
N_BINS           = 72   # Phase 4: was 36 (finer microtonal resolution)

# Shared constants — must match aggregate_all_v12.py exactly
MIN_STABLE_FRAMES = 5
ALPHA             = 0.01  # Phase 2 fix: was 0.5
EPS               = 1e-8

# B1: Tiered margin constants
# MARGIN_STRICT   — above this → HIGH CONFIDENCE, return Top-1 immediately
# ESCALATION_MARGIN — when margin is tight, re-score with dyad-heavy weights
# MIN_MARGIN_FINAL  — below this after escalation → UNKNOWN / LOW CONFIDENCE
MARGIN_STRICT     = 0.003  # BUG-006 fix: was 0.05 (15x too high)
ESCALATION_MARGIN = 0.002  # BUG-006 fix: was 0.02
MIN_MARGIN_FINAL  = 0.001  # BUG-006 fix: was 0.01

# Escalated weights (dyad-heavy) used when Top-2 margin is tight
PCD_WEIGHT_ESC  = 0.3
DYAD_WEIGHT_ESC = 0.7


# =========================
# MODEL LOADING
# =========================

def load_aggregated_models(aggregation_folder):

    models = {}

    pcd_folder  = os.path.join(aggregation_folder, "pcd_stats")
    dyad_folder = os.path.join(aggregation_folder, "dyad_stats")

    if not os.path.exists(pcd_folder) or not os.path.exists(dyad_folder):
        return {}

    for fname in os.listdir(pcd_folder):

        if fname.endswith("_pcd_stats.npz"):

            raga = fname.replace("_pcd_stats.npz", "")

            pcd_path  = os.path.join(pcd_folder, fname)
            dyad_path = os.path.join(dyad_folder, f"{raga}_dyad_stats.npz")

            if not os.path.exists(dyad_path):
                continue

            pcd_data  = np.load(pcd_path,  allow_pickle=True)
            dyad_data = np.load(dyad_path, allow_pickle=True)

            models[raga] = {
                "pcd":       pcd_data["mean_pcd"],
                "mean_up":   dyad_data["mean_up"],
                "mean_down": dyad_data["mean_down"]
            }

    return models


# =========================
# GENERICNESS PENALTY
# =========================

def compute_genericness(pcd):
    """Shannon entropy of the PCD — high entropy = generic/flat distribution."""
    return -np.sum(pcd * np.log(pcd + 1e-10))


# =========================
# DIRECTIONAL DYADS (INFERENCE)
# =========================

def compute_directional_dyads(cents):
    """
    Mirrors compute_directional_dyads_from_gated() in aggregate_all_v12.py
    exactly — same stable-region detection, same MIN_STABLE_FRAMES, same
    Laplace smoothing and normalisation.

    Previously counted every consecutive frame pair as a transition (no
    stability filtering, no smoothing), producing a different signal from
    what the raga signatures were built from. This is the fix.
    """

    bins       = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    if len(pitch_bins) < MIN_STABLE_FRAMES:
        flat = np.zeros(N_BINS * N_BINS)
        return flat, flat

    # --- Stable-region detection (identical to aggregation) ---
    stable_bins = []
    current     = pitch_bins[0]
    count       = 1

    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current = b
            count   = 1

    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)

    mat_up   = np.zeros((N_BINS, N_BINS))
    mat_down = np.zeros((N_BINS, N_BINS))

    for i in range(len(stable_bins) - 1):
        frm = stable_bins[i]
        to  = stable_bins[i + 1]

        if to > frm:
            mat_up[frm, to]   += 1
        elif to < frm:
            mat_down[frm, to] += 1

    # --- Laplace smoothing + normalisation (identical to aggregation) ---
    mat_up   += ALPHA
    mat_down += ALPHA

    mat_up   /= (np.sum(mat_up)   + EPS)
    mat_down /= (np.sum(mat_down) + EPS)

    return mat_up.flatten(), mat_down.flatten()


# =========================
# SCORE ONE PASS
# =========================
# IDF x VARIANCE PCD WEIGHTS (Phase 3 fix: BUG-008 Thodi sink)
# =========================

def compute_pcd_weights(models):
    """
    Compute IDF x variance weights from loaded raga models.
    Downweights common bins, upweights distinctive bins.
    Formula: weight = idf / (std + eps)  [safer form]
    Normalized so weights sum to N_BINS.
    """
    all_pcds = np.array([m["pcd"] for m in models.values()])

    # IDF: bins used by many ragas get low weight
    threshold = 1.0 / N_BINS
    doc_freq = np.sum(all_pcds > threshold, axis=0)
    idf = np.log(len(models) / (doc_freq + 1)) + 1

    # Variance: bins where models agree get low weight
    bin_std = np.std(all_pcds, axis=0)

    # Combined: IDF / (std + eps)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * N_BINS

    return weights


# =========================
# SCORE ONE PASS
# =========================

def _score_models(pcd, test_up, test_down, models, pcd_w, dyad_w,
                  pcd_weights=None):
    """IDF x variance weighted dot-product scoring for all ragas."""
    scores = {}

    # Apply PCD weights if provided (Phase 3 BUG-008 fix)
    if pcd_weights is not None:
        pcd_w_arr = pcd * pcd_weights
        pcd_w_arr = pcd_w_arr / (np.sum(pcd_w_arr) + EPS)
    else:
        pcd_w_arr = pcd

    for raga, model in models.items():

        if pcd_weights is not None:
            model_w = model["pcd"] * pcd_weights
            model_w = model_w / (np.sum(model_w) + EPS)
        else:
            model_w = model["pcd"]

        pcd_sim  = np.dot(pcd_w_arr, model_w)
        up_sim   = np.dot(test_up,  model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])

        dyad_sim = 0.5 * (up_sim + down_sim)

        scores[raga] = pcd_w * pcd_sim + dyad_w * dyad_sim

    return scores


# =========================
# CORE RECOGNITION ENGINE
# =========================

def recognize_raga(audio_path, aggregation_folder, models=None):
    """
    Frozen JSON interface:
        { "final": str, "ranking": list, "margin": float, "confidence_tier": str }

    confidence_tier is one of: "HIGH" | "ESCALATED" | "UNKNOWN"
    The first three fields are unchanged from v1.2 frozen schema.
    """

    try:

        if models is None:
            models = load_aggregated_models(aggregation_folder)

        if not models:
            return {
                "final": "UNKNOWN / LOW CONFIDENCE",
                "ranking": [],
                "margin": 0.0,
                "confidence_tier": "UNKNOWN"
            }

        # ---- Audio load & pitch extraction ----
        y, sr = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)

        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C1"),
            fmax=librosa.note_to_hz("C6"),
            sr=SR,
        )

        valid = f0[~np.isnan(f0)]

        if len(valid) < 200:
            return {
                "final": "UNKNOWN / LOW CONFIDENCE",
                "ranking": [],
                "margin": 0.0,
                "confidence_tier": "UNKNOWN"
            }

        # ---- C1: canonical tonic from utils.py ----
        sa_hz = estimate_tonic(valid)

        cents = 1200 * np.log2(valid / sa_hz)
        cents = cents % 1200

        # ---- PCD ----
        hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))

        if np.sum(hist) == 0:
            return {
                "final": "UNKNOWN / LOW CONFIDENCE",
                "ranking": [],
                "margin": 0.0,
                "confidence_tier": "UNKNOWN"
            }

        pcd = hist / np.sum(hist)

        # ---- Directional Dyads ----
        test_up, test_down = compute_directional_dyads(cents)

        # ================================================================
        # B1: TIERED CONFIDENCE LOGIC
        # Step 1 -- IDF x Variance weighted scoring (Phase 3 BUG-008 fix)
        # ================================================================
        pcd_weights = compute_pcd_weights(models)

        scores = _score_models(pcd, test_up, test_down, models,
                               PCD_WEIGHT, DYAD_WEIGHT,
                               pcd_weights=pcd_weights)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        margin = (ranked[0][1] - ranked[1][1]) if len(ranked) >= 2 else 0.0

        # ================================================================
        # Step 2 — HIGH CONFIDENCE path: margin exceeds strict threshold
        # ================================================================
        if margin >= MARGIN_STRICT:
            return {
                "final": ranked[0][0],
                "ranking": ranked,
                "margin": round(margin, 6),
                "confidence_tier": "HIGH"
            }

        # ================================================================
        # ================================================================
        # Step 3 -- BUG-007 fix: escalation DISABLED (crushed margins 5x)
        # Use first-pass scores with MIN_MARGIN_FINAL threshold instead
        # ================================================================
        if margin >= MIN_MARGIN_FINAL:
            return {
                "final": ranked[0][0],
                "ranking": ranked,
                "margin": round(margin, 6),
                "confidence_tier": "MODERATE"
            }

        # ================================================================
        # Step 4 -- Margin too small -> UNKNOWN
        # ================================================================
        return {
            "final": "UNKNOWN / LOW CONFIDENCE",
            "ranking": ranked,
            "margin": round(margin, 6),
            "confidence_tier": "UNKNOWN"
        }

    except Exception as e:
        print(f"[recognize_raga] ERROR: {e}")
        traceback.print_exc()
        return {
            "final": "UNKNOWN / LOW CONFIDENCE",
            "ranking": [],
            "margin": 0.0,
            "confidence_tier": "UNKNOWN"
        }

