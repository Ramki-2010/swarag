"""
SANDBOX: Phase 1 — PCD-only scoring (DYAD_WEIGHT = 0.0)

Purpose: Stabilize classification by removing broken dyad signal.
Expected: Margins ~2x larger, correct rankings preserved, OOD still rejected.

This script runs the full recognition pipeline with DYAD_WEIGHT=0.0
and compares against the current 0.6/0.4 results.
"""
import sys, os, numpy as np, librosa
sys.path.insert(0, ".")
from utils import estimate_tonic

# ============================================================
# CONFIG — matches recognize_raga_v12.py exactly, except weights
# ============================================================
SR = 22050
MAX_DURATION_SEC = 360
N_BINS = 36
MIN_STABLE_FRAMES = 5
ALPHA = 0.5
EPS = 1e-8

AGG = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260309_082638"
TEST_DIR = r"D:\Swaragam\datasets\audio test"
SEED_DIR = r"D:\Swaragam\datasets\seed_carnatic"

# ============================================================
# FUNCTIONS — copied from recognize_raga_v12.py
# ============================================================

def load_aggregated_models(aggregation_folder):
    models = {}
    pcd_folder = os.path.join(aggregation_folder, "pcd_stats")
    dyad_folder = os.path.join(aggregation_folder, "dyad_stats")
    if not os.path.exists(pcd_folder) or not os.path.exists(dyad_folder):
        return {}
    for fname in os.listdir(pcd_folder):
        if fname.endswith("_pcd_stats.npz"):
            raga = fname.replace("_pcd_stats.npz", "")
            pcd_path = os.path.join(pcd_folder, fname)
            dyad_path = os.path.join(dyad_folder, "{}_dyad_stats.npz".format(raga))
            if not os.path.exists(dyad_path):
                continue
            pcd_data = np.load(pcd_path, allow_pickle=True)
            dyad_data = np.load(dyad_path, allow_pickle=True)
            models[raga] = {
                "pcd": pcd_data["mean_pcd"],
                "mean_up": dyad_data["mean_up"],
                "mean_down": dyad_data["mean_down"],
            }
    return models


def compute_directional_dyads(cents):
    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]
    if len(pitch_bins) < MIN_STABLE_FRAMES:
        flat = np.zeros(N_BINS * N_BINS)
        return flat, flat
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
    for i in range(len(stable_bins) - 1):
        frm = stable_bins[i]
        to = stable_bins[i + 1]
        if to > frm:
            mat_up[frm, to] += 1
        elif to < frm:
            mat_down[frm, to] += 1
    mat_up += ALPHA
    mat_down += ALPHA
    mat_up /= (np.sum(mat_up) + EPS)
    mat_down /= (np.sum(mat_down) + EPS)
    return mat_up.flatten(), mat_down.flatten()


def extract_features(audio_path):
    """Extract PCD and dyads from audio file."""
    y, sr = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C1"),
                            fmax=librosa.note_to_hz("C6"), sr=SR)
    valid = f0[~np.isnan(f0)]
    if len(valid) < 200:
        return None, None, None
    sa_hz = estimate_tonic(valid)
    cents = (1200 * np.log2(valid / sa_hz)) % 1200
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    if np.sum(hist) == 0:
        return None, None, None
    pcd = hist / np.sum(hist)
    test_up, test_down = compute_directional_dyads(cents)
    return pcd, test_up, test_down


def score_all(pcd, test_up, test_down, models, pcd_w, dyad_w):
    """Score against all raga models with given weights."""
    scores = {}
    for raga, model in models.items():
        pcd_sim = np.dot(pcd, model["pcd"])
        up_sim = np.dot(test_up, model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])
        dyad_sim = 0.5 * (up_sim + down_sim)
        scores[raga] = pcd_w * pcd_sim + dyad_w * dyad_sim
    return scores


def classify(scores, margin_high=0.003, margin_min=0.001):
    """Classify with tiered confidence."""
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0.0
    top_score = ranked[0][1]
    mean_score = np.mean([s for _, s in ranked])
    confidence = top_score - mean_score  # OOD metric

    if margin >= margin_high:
        tier = "HIGH"
        prediction = ranked[0][0]
    elif margin >= margin_min:
        tier = "MODERATE"
        prediction = ranked[0][0]
    else:
        tier = "UNKNOWN"
        prediction = "UNKNOWN / LOW CONFIDENCE"

    return prediction, tier, margin, confidence, ranked


# ============================================================
# RUN TESTS
# ============================================================

models = load_aggregated_models(AGG)
print("Loaded {} raga models: {}".format(len(models), ", ".join(sorted(models.keys()))))
print()

# --- Random test files ---
test_files = [
    ("Alapana_HAM_Test.wav", "OOD (Hamsadwani)"),
    ("Alapana_Moha_Test.wav", "OOD (Mohanam)"),
    ("Balap_Test.wav", "Bhairavi"),
    ("Kalap_Test.wav", "Kalyani"),
]

print("=" * 80)
print("PHASE 1: PCD-ONLY vs CURRENT (0.6/0.4)")
print("=" * 80)

# Header
print()
print("{:25} {:15} | {:>8} {:>8} {:>8} | {:>8} {:>8} {:>8} | {:>8}".format(
    "File", "Expected",
    "Cur_Top1", "Cur_Marg", "Cur_Tier",
    "PCD_Top1", "PCD_Marg", "PCD_Tier",
    "OOD_Conf"))
print("-" * 120)

for fname, expected in test_files:
    fpath = os.path.join(TEST_DIR, fname)
    pcd, test_up, test_down = extract_features(fpath)
    if pcd is None:
        print("{:25} FAILED TO EXTRACT".format(fname))
        continue

    # Current scoring (0.6 PCD / 0.4 Dyad)
    scores_cur = score_all(pcd, test_up, test_down, models, 0.6, 0.4)
    pred_cur, tier_cur, margin_cur, _, _ = classify(scores_cur)

    # PCD-only scoring (1.0 PCD / 0.0 Dyad)
    scores_pcd = score_all(pcd, test_up, test_down, models, 1.0, 0.0)
    pred_pcd, tier_pcd, margin_pcd, conf_pcd, ranked_pcd = classify(scores_pcd)

    # Status
    print("{:25} {:15} | {:>8} {:8.4f} {:>8} | {:>8} {:8.4f} {:>8} | {:8.4f}".format(
        fname[:25], expected,
        pred_cur[:8], margin_cur, tier_cur,
        pred_pcd[:8], margin_pcd, tier_pcd,
        conf_pcd))

# --- Seed dataset evaluation ---
print()
print("=" * 80)
print("SEED DATASET: PCD-ONLY SELF-RECOGNITION")
print("=" * 80)

correct_high = 0
correct_mod = 0
correct_unknown = 0
wrong = 0
total = 0

raga_results = {}

for raga in sorted(os.listdir(SEED_DIR)):
    raga_dir = os.path.join(SEED_DIR, raga)
    if not os.path.isdir(raga_dir):
        continue
    raga_results[raga] = {"correct": 0, "wrong": 0, "unknown": 0, "margins": []}

    for audio_file in sorted(os.listdir(raga_dir)):
        if not audio_file.endswith((".wav", ".mp3", ".flac")):
            continue
        fpath = os.path.join(raga_dir, audio_file)
        pcd, test_up, test_down = extract_features(fpath)
        if pcd is None:
            continue

        total += 1
        scores_pcd = score_all(pcd, test_up, test_down, models, 1.0, 0.0)
        pred, tier, margin, conf, ranked = classify(scores_pcd)

        if pred == raga:
            if tier == "HIGH":
                correct_high += 1
            else:
                correct_mod += 1
            raga_results[raga]["correct"] += 1
        elif pred == "UNKNOWN / LOW CONFIDENCE":
            correct_unknown += 1
            raga_results[raga]["unknown"] += 1
            # Check if ranking is still correct
            if ranked[0][0] == raga:
                raga_results[raga]["correct"] += 1  # ranking correct even if UNKNOWN
        else:
            wrong += 1
            raga_results[raga]["wrong"] += 1
            print("  WRONG: {} -> {} (expected {}, margin={:.4f})".format(
                audio_file[:40], pred, raga, margin))

        raga_results[raga]["margins"].append(margin)

print()
print("SEED RESULTS SUMMARY (PCD-only, 1.0/0.0):")
print("-" * 60)
for raga in sorted(raga_results.keys()):
    r = raga_results[raga]
    n = r["correct"] + r["wrong"] + r["unknown"]
    margins = r["margins"]
    mean_m = np.mean(margins) if margins else 0
    print("  {:20} n={:2d} correct={:2d} wrong={:2d} unknown={:2d} mean_margin={:.4f}".format(
        raga, n, r["correct"], r["wrong"], r["unknown"], mean_m))

print()
print("TOTALS:")
print("  Total files:    {}".format(total))
print("  HIGH confidence: {}".format(correct_high))
print("  MODERATE:        {}".format(correct_mod))
print("  UNKNOWN:         {}".format(correct_unknown))
print("  WRONG:           {}".format(wrong))
print("  Accuracy (excl UNKNOWN): {:.1f}%".format(
    100 * (correct_high + correct_mod) / max(1, correct_high + correct_mod + wrong)))
